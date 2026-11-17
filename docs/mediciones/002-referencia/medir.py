"""Aceptación002 con la instantánea publicada utilizada por003."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from src.orchestrator.bench_niebla import bench_referencia_publicada
paquete = RAIZ / 'docs/mediciones/003-reporte/003-resolubilidad-publicada-paquete.json'
resultado = bench_referencia_publicada(json.loads(paquete.read_text()))
resultado['paquete'] = str(paquete.relative_to(RAIZ))
resultado['sha256'] = hashlib.sha256(paquete.read_bytes()).hexdigest()
resultado['commit_base'] = subprocess.check_output(['git','rev-parse','HEAD'], cwd=RAIZ, text=True).strip()
salida = Path(__file__).with_name('resultado.json')
salida.write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:resultado[k] for k in ('id','version','V','E','max_ms','fallos_5ms','revelaciones')},ensure_ascii=False))
