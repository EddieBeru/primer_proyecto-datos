"""Almacén persistente de fichas del catálogo (§4.3/§4.4 doc oficial).

La caché LRU en memoria tiene tope ``--cache-size``; cuando desaloja una
ficha, la ficha sigue aquí: recuperarla cuesta una lectura de disco y
NUNCA otra solicitud de red, salvo que jamás se haya persistido o que la
versión del catálogo ya no coincida.

Formato propio (append-only, un registro por ficha):

    MAGIA (9 bytes) + fmt(1) + largo(B, u32) + pickle(version)
    registro: largo(u32) + pickle((id, ficha))

El índice id -> offset vive en memoria como ``TablaHash`` propia (solo
metadatos: las fichas no se mantienen en RAM; cada ``obtener`` hace una
lectura de disco). Con ``ruta=None`` el almacén vive solo en memoria
(pruebas / sesiones sin persistencia).
"""

from __future__ import annotations

import os
import pickle
import struct

from src.controller1.lista_doble import Nodo
from src.controller1.tabla_hash import TablaHash

MAGIA = b"CRIPTAFX\x00"
FMT = 1
_LARGO = struct.Struct("<I")


class AlmacenFichas:
    """Fichas del catálogo persistidas aparte del tope de la LRU."""

    def __init__(self, ruta: str | None = None, version: str | None = None) -> None:
        self.ruta = ruta
        self.version = version
        self._indice = TablaHash()
        self._reiniciar = False  # al invalidar, el próximo guardar trunca

    def __len__(self) -> int:
        return len(self._indice)

    def contiene(self, entidad_id: str) -> bool:
        return self._indice.obtener(entidad_id) is not None

    def obtener(self, entidad_id: str):
        """Ficha desde disco (o memoria si no hay ruta). None si no está."""
        nodo = self._indice.obtener(entidad_id)
        if nodo is None:
            return None
        if self.ruta is None:
            return nodo.valor
        try:
            with open(self.ruta, "rb") as f:
                f.seek(int(nodo.valor))
                crudo = f.read(4)
                if len(crudo) < 4:
                    return None
                (largo,) = _LARGO.unpack(crudo)
                payload = f.read(largo)
                if len(payload) < largo:
                    return None
                _, ficha = pickle.loads(payload)
                return ficha
        except (OSError, struct.error, pickle.PickleError, EOFError, ValueError):
            return None

    def guardar(self, entidad_id: str, ficha) -> None:
        """Persiste (o reemplaza) la ficha. Idempotente por id."""
        if self.ruta is None:
            self._indice.poner(entidad_id, Nodo(entidad_id, ficha))
            return
        self._asegurar_archivo()
        payload = pickle.dumps((entidad_id, ficha), protocol=4)
        with open(self.ruta, "ab") as f:
            offset = f.tell()
            f.write(_LARGO.pack(len(payload)))
            f.write(payload)
        self._indice.poner(entidad_id, Nodo(entidad_id, offset))

    def guardar_lote(self, pares) -> None:
        for entidad_id, ficha in pares:
            self.guardar(entidad_id, ficha)

    def invalida_si_cambia(self, nueva_version: str | None) -> bool:
        """True si la versión cambió (almacén vaciado); False si sigue válido."""
        if nueva_version == self.version:
            return False
        self.version = nueva_version
        self._indice = TablaHash()
        self._reiniciar = True
        return True

    # -- disco completo (sesión) --
    def _asegurar_archivo(self) -> None:
        if not self._reiniciar and os.path.isfile(self.ruta):
            return
        cabecera = pickle.dumps(self.version, protocol=4)
        with open(self.ruta, "wb") as f:
            f.write(MAGIA)
            f.write(bytes([FMT]))
            f.write(_LARGO.pack(len(cabecera)))
            f.write(cabecera)
        self._reiniciar = False

    @classmethod
    def cargar_disco(cls, ruta: str) -> "AlmacenFichas":
        """Reconstruye el índice de offsets sin cargar las fichas a memoria."""
        almacen = cls(ruta=ruta)
        try:
            with open(ruta, "rb") as f:
                if f.read(len(MAGIA)) != MAGIA:
                    raise ValueError(f"almacén con formato desconocido: {ruta}")
                fmt = f.read(1)
                if not fmt or fmt[0] != FMT:
                    raise ValueError(f"almacén con versión de formato desconocida: {ruta}")
                crudo = f.read(4)
                if len(crudo) < 4:
                    raise ValueError(f"almacén truncado: {ruta}")
                (largo,) = _LARGO.unpack(crudo)
                almacen.version = pickle.loads(f.read(largo))
                while True:
                    offset = f.tell()
                    crudo = f.read(4)
                    if len(crudo) < 4:
                        break
                    (largo,) = _LARGO.unpack(crudo)
                    payload = f.read(largo)
                    if len(payload) < largo:
                        break  # registro truncado: se ignora el final
                    try:
                        entidad_id, _ = pickle.loads(payload)
                    except (pickle.PickleError, EOFError, ValueError):
                        continue
                    almacen._indice.poner(entidad_id, Nodo(entidad_id, offset))
        except OSError as e:
            raise ValueError(f"no se pudo leer el almacén: {e}") from e
        return almacen
