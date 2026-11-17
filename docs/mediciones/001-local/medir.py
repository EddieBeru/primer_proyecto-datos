"""Decisión fresca de rango pequeño con actor distante y localización indexada."""
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from src.orchestrator.bench import _crear_cripta_bench, _catalogo_cazadores
from src.controller2.modelo import EnemigoInstancia
from src.controller2.fachada import Fachada
from src.controller2.enemigos import decidir_accion_cazador
from src.controller1.mergesort import mergesort
filas = []
for n in (100,10000):
    estado = _crear_cripta_bench(n)
    estado.salas[n-1].enemigos.append(EnemigoInstancia('distante','cazador-pequeno',20,n-1))
    catalogo = _catalogo_cazadores()
    fachada = Fachada(estado, object(), catalogo)
    def decidir():
        ubicacion = fachada._ubicar_enemigo('distante')
        ubicacion[1]._ruta_cazador = None
        return decidir_accion_cazador(estado,'distante',catalogo,ubicacion=ubicacion)
    for _ in range(100): decidir()
    muestras = []
    for _ in range(1000):
        inicio = perf_counter_ns()
        resultado = decidir()
        muestras.append((perf_counter_ns()-inicio)/1e6)
        assert resultado == ('esperar',100,None)
    orden = mergesort(muestras)
    filas.append({'V':n,'sala_cazador':n-1,'sala_jugador':1,'rango':catalogo['cazador-pequeno'].rango,
                  'muestras_ms':muestras,'mediana_ms':orden[len(orden)//2],'max_ms':orden[-1]})
salida={'python':platform.python_version(),'maquina':platform.platform(),
        'commit_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=RAIZ,text=True).strip(),
        'metodo':'100 calentamientos,1000 decisiones frescas por mapa; localizacion indexada incluida; preparacion fuera del reloj',
        'filas':filas}
Path(__file__).with_name('resultado.json').write_text(json.dumps(salida,ensure_ascii=False,indent=2)+'\n')
print([(f['V'],f['mediana_ms'],f['max_ms']) for f in filas])
