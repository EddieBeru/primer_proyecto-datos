"""C1-8 Guardado binario (§4.10 doc oficial).

v1 (compat): formato simple original para dicts legado
  {cripta_id, version_cripta, version_catalogo, sala_actual, vida, ...}.
v2 (oficial): binario propio con índice de salas para acceso aleatorio:
  MAGIA + ver(2) + n_salas(H) + [(sala_id(i), offset(q), largo(q))...]
  + core_len(q) + core_json + blobs sala_json...
  core = todo EstadoPartida.a_dict() menos "salas". Incluye semilla,
  azar_llamadas/azar_estado (base64), reloj, agenda, pila, contadores.
Dañado/truncado/version -> GuardadoError, nunca crash.
"""

from __future__ import annotations

import base64
import io
import json
import os
import struct
import time

from src.controller1 import endpoints
from src.controller1.mergesort import mergesort
from src.models.errors import GuardadoError

MAGIA = b"CRIPTA\x00"
VERSION_FMT = 3
VERSION_FMT_V2 = 2
VERSION_FMT_V1 = 1
_ENTERO = struct.Struct("<i")


def _pack_str(datos, texto):
    raw = texto.encode("utf-8")
    datos += struct.pack("<I", len(raw)) + raw


def _unpack_str(buf, pos):
    if pos + 4 > len(buf):
        raise GuardadoError("archivo truncado")
    (largo,) = struct.unpack_from("<I", buf, pos)
    pos += 4
    if pos + largo > len(buf):
        raise GuardadoError("archivo truncado")
    return buf[pos:pos + largo].decode("utf-8"), pos + largo


def _es_legado(estado: dict) -> bool:
    return "vida" in estado and "jugador" not in estado


def _json_blob(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")


# -- v1 compat -----------------------------------------------------------

def _guardar_v1(ruta, estado):
    try:
        datos = bytearray(MAGIA)
        datos += struct.pack("<B", VERSION_FMT_V1)
        for campo in ("cripta_id", "version_cripta", "version_catalogo"):
            _pack_str(datos, estado[campo])
        for campo in ("sala_actual", "vida", "vida_max", "ataque",
                      "defensa", "velocidad", "presupuesto"):
            datos += _ENTERO.pack(estado[campo])
        inventario = estado.get("inventario", [])
        datos += struct.pack("<H", len(inventario))
        for item in inventario:
            _pack_str(datos, item)
        with open(ruta, "wb") as f:
            f.write(bytes(datos))
    except (OSError, struct.error, KeyError, TypeError) as e:
        raise GuardadoError(f"no se pudo guardar: {e}") from e


def _cargar_v1(buf: bytes):
    pos = len(MAGIA) + 1
    try:
        estado = {}
        for campo in ("cripta_id", "version_cripta", "version_catalogo"):
            estado[campo], pos = _unpack_str(buf, pos)
        for campo in ("sala_actual", "vida", "vida_max", "ataque",
                      "defensa", "velocidad", "presupuesto"):
            if pos + 4 > len(buf):
                raise GuardadoError("archivo truncado")
            (estado[campo],) = _ENTERO.unpack_from(buf, pos)
            pos += 4
        if pos + 2 > len(buf):
            raise GuardadoError("archivo truncado")
        (n_items,) = struct.unpack_from("<H", buf, pos)
        pos += 2
        inventario = []
        for _ in range(n_items):
            item, pos = _unpack_str(buf, pos)
            inventario.append(item)
        estado["inventario"] = inventario
        return estado
    except GuardadoError:
        raise
    except (struct.error, UnicodeDecodeError) as e:
        raise GuardadoError(f"archivo dañado: {e}") from e


# -- v2 oficial ----------------------------------------------------------

def _core_sin_salas(estado: dict) -> dict:
    core = dict(estado)
    core.pop("salas", None)
    ae = core.get("azar_estado")
    if ae is not None and not isinstance(ae, (str, list, type(None))):
        try:
            # tuple getstate -> lista serializable (bytes -> b64)
            ver, inner, gauss = ae
            inner = list(inner)
            core["azar_estado"] = {"v": ver, "inner": inner, "g": gauss}
        except Exception:
            core["azar_estado"] = None
    return core


def _restaurar_azar(core: dict) -> dict:
    ae = core.get("azar_estado")
    if isinstance(ae, dict) and "inner" in ae:
        core["azar_estado"] = (ae["v"], tuple(ae["inner"]), ae.get("g"))
    return core


def guardar(ruta, estado):
    """P2 escribe v3; conservar escritura técnica de dicts legados v1/v2."""
    if _es_legado(estado):
        return _guardar_v1(ruta, estado)
    try:
        salas = estado.get("salas") or {}
        blobs = {str(k): _json_blob(v) for k, v in salas.items()}
        core = _json_blob(_core_sin_salas(estado))
        n = len(blobs)
        # header + índice
        version = 4 if "historia" in estado else VERSION_FMT if "conocimiento" in estado else VERSION_FMT_V2
        if any(sala.get("contenido_pendiente", False) for sala in salas.values()) or b'"contenido_pendiente"' in core:
            version = 5
        formato_indice = "<qqq" if version >= 3 else "<iqq"
        idx = struct.pack(f"<{len(MAGIA)}sBH", MAGIA, version, n)
        entradas = b""
        base = len(idx) + n * struct.calcsize(formato_indice) + struct.calcsize("<q")
        off = base + len(core)
        # §4.9: índice de salas ordenado con el mergesort propio (sin sorted).
        orden = mergesort(list(blobs.items()), clave=lambda kv: int(kv[0]))
        for sid, blob in orden:
            entradas += struct.pack(formato_indice, int(sid), off, len(blob))
            off += len(blob)
        with open(ruta, "wb") as f:
            f.write(idx)
            f.write(entradas)
            f.write(struct.pack("<q", len(core)))
            f.write(core)
            for _, blob in orden:
                f.write(blob)
    except (OSError, struct.error, KeyError, TypeError, ValueError) as e:
        raise GuardadoError(f"no se pudo guardar: {e}") from e


def _leer_indice(buf: bytes):
    from src.estructuras.tabla_indice import TablaIndice
    pos = len(MAGIA) + 1
    version = buf[len(MAGIA)]
    formato = "<qqq" if version >= 3 else "<iqq"
    ancho = struct.calcsize(formato)
    (n,) = struct.unpack_from("<H", buf, pos)
    pos += 2
    entradas = TablaIndice()
    ultimo_id = None
    for _ in range(n):
        sid, off, largo = struct.unpack_from(formato, buf, pos)
        pos += ancho
        if sid in entradas or (ultimo_id is not None and sid <= ultimo_id):
            raise GuardadoError("índice de salas duplicado o desordenado")
        entradas[sid] = (off, largo)
        ultimo_id = sid
    (core_len,) = struct.unpack_from("<q", buf, pos)
    pos += 8
    if core_len < 0 or pos + core_len > len(buf):
        raise GuardadoError("core truncado o inválido")
    core = json.loads(buf[pos:pos + core_len].decode("utf-8"))
    if type(core) is not dict:
        raise GuardadoError("core debe ser objeto JSON")
    regiones = mergesort(list(entradas.items()), clave=lambda kv: kv[1][0])
    fin = pos + core_len
    for sid, (off, largo) in regiones:
        if off != fin or largo < 0 or off + largo > len(buf):
            raise GuardadoError("índice solapado, truncado o inválido")
        fin = off + largo
    if fin != len(buf):
        raise GuardadoError("datos adicionales fuera del índice")
    return entradas, _restaurar_azar(core)


def cargar(ruta):
    """Lector técnico v1/v2/v3; el flujo de partida P2 usa cargar_p2."""
    try:
        with open(ruta, "rb") as f:
            buf = f.read()
        if not buf.startswith(MAGIA):
            raise GuardadoError("no es archivo de partida")
        if len(buf) <= len(MAGIA):
            raise GuardadoError("archivo truncado")
        ver = buf[len(MAGIA)]
        if ver == VERSION_FMT_V1:
            return _cargar_v1(buf)
        if ver not in (VERSION_FMT_V2, VERSION_FMT, 4, 5):
            raise GuardadoError("versión de formato desconocida")
        entradas, core = _leer_indice(buf)
        salas = {}
        for sid, (off, largo) in entradas.items():
            sala = json.loads(buf[off:off+largo].decode("utf-8"))
            if type(sala) is not dict or sala.get("id") != sid:
                raise GuardadoError("ID de sala no coincide con índice")
            salas[str(sid)] = sala
        core["salas"] = salas
        return core
    except GuardadoError:
        raise
    except (OSError, struct.error, UnicodeDecodeError, ValueError, TypeError) as e:
        raise GuardadoError(f"archivo dañado o ilegible: {e}") from e


def cargar_p2(ruta):
    """Rechazar guardados anteriores sin inventar conocimiento perdido."""
    try:
        with open(ruta, "rb") as f:
            head = f.read(len(MAGIA) + 1)
        if not head.startswith(MAGIA) or len(head) != len(MAGIA) + 1:
            raise GuardadoError("archivo de partida inválido o truncado")
        if head[-1] in (1, 2):
            raise GuardadoError("guardado v1/v2 incompatible con P2: se requiere v3 con conocimiento")
        return cargar(ruta)
    except OSError as e:
        raise GuardadoError(f"no se pudo leer: {e}") from e


def cargar_sala(ruta, sala_id: int):
    """Acceso por índice a una sala; no lee los demás blobs ni el core JSON."""
    try:
        with open(ruta, "rb") as f:
            head = f.read(len(MAGIA)+3)
            if len(head) != len(MAGIA)+3 or not head.startswith(MAGIA):
                raise GuardadoError("archivo inválido o truncado")
            version = head[len(MAGIA)]
            if version not in (2, 3, 4, 5):
                raise GuardadoError("formato sin índice compatible")
            formato = "<qqq" if version >= 3 else "<iqq"
            ancho = struct.calcsize(formato)
            n = struct.unpack_from("<H", head, len(MAGIA)+1)[0]
            elegido, anterior = None, None
            fin_previo = None
            for _ in range(n):
                raw = f.read(ancho)
                sid, off, largo = struct.unpack(formato, raw)
                if anterior is not None and sid <= anterior:
                    raise GuardadoError("índice duplicado o desordenado")
                if largo < 0 or (fin_previo is not None and off != fin_previo):
                    raise GuardadoError("índice inválido")
                anterior, fin_previo = sid, off+largo
                if sid == sala_id:
                    elegido = (off, largo)
            raw = f.read(8)
            core_len = struct.unpack("<q", raw)[0]
            minimo = f.tell()+core_len
            if elegido is None:
                raise GuardadoError(f"sala {sala_id} no está en el archivo")
            off, largo = elegido
            if core_len < 0 or off < minimo or off+largo > os.fstat(f.fileno()).st_size:
                raise GuardadoError("índice fuera del archivo")
            f.seek(off)
            sala = json.loads(f.read(largo).decode("utf-8"))
            if type(sala) is not dict or sala.get("id") != sala_id:
                raise GuardadoError("ID de sala no coincide con índice")
            return sala
    except GuardadoError:
        raise
    except (OSError, struct.error, UnicodeDecodeError, ValueError, TypeError) as e:
        raise GuardadoError(f"archivo dañado o ilegible: {e}") from e


def comparar_json(estado: dict) -> dict:
    """Tamaño en disco y tiempo de carga binario vs JSON (§4.10)."""
    import tempfile
    blob_json = _json_blob(estado)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as fb, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".json") as fj:
        rb, rj = fb.name, fj.name
    try:
        guardar(rb, estado)
        with open(rj, "wb") as f:
            f.write(blob_json)
        t0 = time.perf_counter()
        cargar(rb)
        t_bin = time.perf_counter() - t0
        t0 = time.perf_counter()
        json.loads(blob_json.decode("utf-8"))
        t_json = time.perf_counter() - t0
        return {"bin_bytes": os.path.getsize(rb), "json_bytes": os.path.getsize(rj),
                "bin_carga_s": t_bin, "json_carga_s": t_json}
    finally:
        for p in (rb, rj):
            try:
                os.unlink(p)
            except OSError:
                pass


def validar_versiones(estado, budget=None, backend=None):
    """Compara versiones guardadas vs disponibles (endpoints 3 y 6 u offline/fake)."""
    be = backend or endpoints
    ver_cripta = be.version_cripta(estado["cripta_id"], budget)
    ver_cat = be.version_catalogo(budget)
    return (ver_cripta.version == estado["version_cripta"],
            ver_cat.version == estado["version_catalogo"])


def cargar_historia(ruta):
    """Flujo004: historia completa en4/5; lector técnico separado."""
    try:
        with open(ruta, 'rb') as archivo:
            cabecera=archivo.read(len(MAGIA)+1)
        if len(cabecera) != len(MAGIA)+1 or cabecera[:len(MAGIA)] != MAGIA:
            raise GuardadoError('guardado inválido')
        if cabecera[-1] not in (4, 5):
            raise GuardadoError('guardado v1/v2/v3 incompatible: se requiere v4 con historia completa')
        data=cargar(ruta)
        if type(data.get('historia')) is not dict: raise GuardadoError('historia ausente')
        return data
    except OSError as exc:
        raise GuardadoError(str(exc)) from exc
