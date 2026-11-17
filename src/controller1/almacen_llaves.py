"""Persistencia atómica del DTO versionado de ubicaciones."""

import json
import os
import tempfile

from src.models.resolubilidad import UbicacionesLlaves


class AlmacenLlaves:
    def __init__(self, ruta):
        self.ruta = ruta

    def obtener(self, cripta_id, version):
        try:
            with open(self.ruta, encoding="utf-8") as archivo:
                dato = json.load(archivo)
            if type(dato) is not dict or dato.get("formato") != 1:
                return None
            dto = UbicacionesLlaves.desde_dict(dato)
        except (OSError, ValueError, TypeError, KeyError):
            return None
        if dto.cripta_id != cripta_id or dto.version_cripta != version or not dto.completa:
            return None
        return dto

    def guardar(self, dto):
        if not isinstance(dto, UbicacionesLlaves) or not dto.completa:
            raise ValueError("solo se persisten respuestas completas")
        carpeta = os.path.dirname(os.path.abspath(self.ruta))
        fd, temporal = tempfile.mkstemp(prefix=".llaves-", dir=carpeta, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as archivo:
                json.dump({"formato": 1, "cripta_id": dto.cripta_id,
                    "version_cripta": dto.version_cripta, "completa": dto.completa,
                    "llaves": [{"id": x.id, "sala": x.sala, "enemigo": x.enemigo}
                               for x in dto.llaves]}, archivo, ensure_ascii=False)
                archivo.flush()
                os.fsync(archivo.fileno())
            os.replace(temporal, self.ruta)
        finally:
            if os.path.exists(temporal):
                os.unlink(temporal)
