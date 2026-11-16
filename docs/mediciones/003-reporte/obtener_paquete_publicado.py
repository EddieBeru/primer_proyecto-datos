"""Descarga una instantánea del mayor esqueleto publicado para T044.

Conserva la respuesta cruda de /llaves: el despliegue actual no incluye los
metadatos de versión/completitud exigidos por el contrato de003.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

from config.settings import URL_BASE
from src.controller1.client import Client
from src.controller1.endpoints import listar_criptas


SALIDA = Path(__file__).with_name("003-resolubilidad-publicada-paquete.json")


def main():
    lista = listar_criptas().criptas
    mayor = max(lista, key=lambda cripta: cripta.salas)
    cliente = Client()
    general = cliente.make_request(f"criptas/{mayor.id}")
    paginas = []
    for pagina in range(1, general["paginas"] + 1):
        paginas.append(cliente.make_request(
            f"criptas/{mayor.id}/salas?pagina={pagina}"))
    llaves = cliente.make_request(f"criptas/{mayor.id}/llaves")
    paquete = {
        "capturado_utc": datetime.now(timezone.utc).isoformat(),
        "origen": URL_BASE,
        "cripta": {"id": mayor.id, "nombre": mayor.nombre,
                   "salas_lista": mayor.salas},
        "general": general,
        "paginas_esqueleto": paginas,
        "respuesta_llaves_cruda": llaves,
    }
    contenido = json.dumps(paquete, ensure_ascii=False, indent=2) + "\n"
    SALIDA.write_text(contenido, encoding="utf-8")
    resumen = {"archivo": str(SALIDA), "bytes": SALIDA.stat().st_size,
               "sha256": hashlib.sha256(SALIDA.read_bytes()).hexdigest(),
               "id": mayor.id, "nombre": mayor.nombre,
               "salas": mayor.salas, "version": general["version"],
               "paginas": len(paginas),
               "llaves": len(llaves.get("llaves", ())),
               "llaves_metadata": [k for k in llaves
                                   if k != "llaves"]}
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
