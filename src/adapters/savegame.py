"""C1-8 Guardado y carga binaria de partida (Flujo G).

Formato propio con struct (provisional: la lista final del estado K2
la fija C2; agenda/pila/instancias entran cuando C2 las entregue):
  magia(7s) version_fmt(B) cripta_id str version_cripta str
  version_catalogo str sala_actual(i) vida(i) vida_max(i) ataque(i)
  defensa(i) velocidad(i) presupuesto(i) n_items(H) items[str...]
str = largo(I) + utf-8. Dañado/truncado → GuardadoError, nunca crash.
"""

import struct

from src.api import endpoints
from src.models.errors import GuardadoError

MAGIA = b"CRIPTA\x00"
VERSION_FMT = 1
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


def guardar(ruta, estado):
    """estado: dict con cripta_id, version_cripta, version_catalogo,
    sala_actual, vida, vida_max, ataque, defensa, velocidad,
    presupuesto, inventario (lista de ids)."""
    try:
        datos = bytearray(MAGIA)
        datos += struct.pack("<B", VERSION_FMT)
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


def cargar(ruta):
    try:
        with open(ruta, "rb") as f:
            buf = f.read()
    except OSError as e:
        raise GuardadoError(f"no se pudo leer: {e}") from e
    if not buf.startswith(MAGIA):
        raise GuardadoError("no es archivo de partida")
    pos = len(MAGIA)
    if pos >= len(buf) or buf[pos] != VERSION_FMT:
        raise GuardadoError("versión de formato desconocida")
    pos += 1
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


def validar_versiones(estado, budget=None):
    """Compara versiones guardadas vs servidor (endpoints 3 y 6).

    Retorna (cripta_ok, catalogo_ok). 2 peticiones baratas que evitan
    jugar con datos desactualizados (Flujo G).
    """
    ver_cripta = endpoints.version_cripta(estado["cripta_id"], budget)
    ver_cat = endpoints.version_catalogo(budget)
    return (ver_cripta.version == estado["version_cripta"],
            ver_cat.version == estado["version_catalogo"])
