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

from src.api import endpoints
from src.models.errors import GuardadoError

MAGIA = b"CRIPTA\x00"
VERSION_FMT = 2
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
    """Acepta dict legado (v1) o dict EstadoPartida.a_dict() (v2)."""
    if _es_legado(estado):
        return _guardar_v1(ruta, estado)
    try:
        salas = estado.get("salas") or {}
        blobs = {str(k): _json_blob(v) for k, v in salas.items()}
        core = _json_blob(_core_sin_salas(estado))
        n = len(blobs)
        # header + índice
        idx = struct.pack(f"<{len(MAGIA)}sBH", MAGIA, VERSION_FMT, n)
        entradas = b""
        base = len(idx) + n * struct.calcsize("<iqq") + struct.calcsize("<q")
        off = base + len(core)
        orden = sorted(blobs.items(), key=lambda kv: int(kv[0]))
        for sid, blob in orden:
            entradas += struct.pack("<iqq", int(sid), off, len(blob))
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
    pos = len(MAGIA) + 1
    (n,) = struct.unpack_from("<H", buf, pos)
    pos += 2
    entradas = {}
    for _ in range(n):
        if pos + 20 > len(buf):
            raise GuardadoError("archivo truncado")
        sid, off, largo = struct.unpack_from("<iqq", buf, pos)
        pos += 20
        entradas[int(sid)] = (off, largo)
    if pos + 8 > len(buf):
        raise GuardadoError("archivo truncado")
    (core_len,) = struct.unpack_from("<q", buf, pos)
    pos += 8
    if pos + core_len > len(buf):
        raise GuardadoError("archivo truncado")
    core = json.loads(buf[pos:pos + core_len].decode("utf-8"))
    return entradas, _restaurar_azar(core)


def cargar(ruta):
    try:
        with open(ruta, "rb") as f:
            buf = f.read()
    except OSError as e:
        raise GuardadoError(f"no se pudo leer: {e}") from e
    if not buf.startswith(MAGIA):
        raise GuardadoError("no es archivo de partida")
    pos = len(MAGIA)
    if pos >= len(buf):
        raise GuardadoError("archivo truncado")
    ver = buf[pos]
    if ver == VERSION_FMT_V1:
        return _cargar_v1(buf)
    if ver != VERSION_FMT:
        raise GuardadoError("versión de formato desconocida")
    try:
        pos = len(MAGIA) + 1
        (n,) = struct.unpack_from("<H", buf, pos)
        pos += 2
        entradas = {}
        for _ in range(n):
            if pos + 20 > len(buf):
                raise GuardadoError("archivo truncado")
            sid, off, largo = struct.unpack_from("<iqq", buf, pos)
            pos += 20
            entradas[int(sid)] = (off, largo)
        if pos + 8 > len(buf):
            raise GuardadoError("archivo truncado")
        (core_len,) = struct.unpack_from("<q", buf, pos)
        pos += 8
        if pos + core_len > len(buf):
            raise GuardadoError("archivo truncado")
        core = _restaurar_azar(json.loads(buf[pos:pos + core_len].decode("utf-8")))
        salas = {}
        for sid, (off, largo) in entradas.items():
            if off + largo > len(buf):
                raise GuardadoError("archivo truncado")
            salas[str(sid)] = json.loads(buf[off:off + largo].decode("utf-8"))
        core["salas"] = salas
        return core
    except GuardadoError:
        raise
    except (struct.error, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise GuardadoError(f"archivo dañado: {e}") from e


def cargar_sala(ruta, sala_id: int):
    """Recupera una sala sin leer el archivo completo (§4.10)."""
    try:
        with open(ruta, "rb") as f:
            head = f.read(len(MAGIA) + 1 + 2)
            if not head.startswith(MAGIA):
                raise GuardadoError("no es archivo de partida")
            ver = head[len(MAGIA)]
            if ver == VERSION_FMT_V1:
                raise GuardadoError("formato v1 sin índice; convierta a v2")
            if ver != VERSION_FMT:
                raise GuardadoError("versión de formato desconocida")
            (n,) = struct.unpack_from("<H", head, len(MAGIA) + 1)
            entradas = {}
            for _ in range(n):
                raw = f.read(20)
                if len(raw) < 20:
                    raise GuardadoError("archivo truncado")
                sid, off, largo = struct.unpack("<iqq", raw)
                entradas[int(sid)] = (off, largo)
            if sala_id not in entradas:
                raise GuardadoError(f"sala {sala_id} no está en el archivo")
            off, largo = entradas[int(sala_id)]
            f.seek(off)
            blob = f.read(largo)
            if len(blob) < largo:
                raise GuardadoError("archivo truncado")
            return json.loads(blob.decode("utf-8"))
    except GuardadoError:
        raise
    except OSError as e:
        raise GuardadoError(f"no se pudo leer: {e}") from e


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


def validar_versiones(estado, budget=None):
    """Compara versiones guardadas vs servidor (endpoints 3 y 6)."""
    ver_cripta = endpoints.version_cripta(estado["cripta_id"], budget)
    ver_cat = endpoints.version_catalogo(budget)
    return (ver_cripta.version == estado["version_cripta"],
            ver_cat.version == estado["version_catalogo"])
