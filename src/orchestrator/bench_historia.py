"""FR-LIN-13/14: 5000 acciones y tres K frente a reconstrucción sin checkpoints."""
import json
import platform
import time
import tracemalloc
import sys
from src.estructuras.tabla_indice import TablaIndice
from src.controller1.mergesort import mergesort
from src.controller2.linea_tiempo import LineaTiempo
from src.controller2.modelo import EstadoPartida, JugadorVivo, SalaViva
from src.models.conocimiento import DatosSala


def bytes_estructura(valor, vistos=None):
    """Tamaño retenido del grafo Python, deduplicando referencias con índice propio."""
    if vistos is None: vistos=TablaIndice()
    identidad=id(valor)
    if identidad in vistos: return 0
    vistos[identidad]=True
    total=sys.getsizeof(valor)
    if isinstance(valor,dict):
        for k,v in valor.items(): total+=bytes_estructura(k,vistos)+bytes_estructura(v,vistos)
    elif isinstance(valor,(tuple,list)):
        for v in valor: total+=bytes_estructura(v,vistos)
    return total


def medir_memoria(linea):
    datos=linea.a_dict()
    def tamano(v): return len(json.dumps(v,separators=(',',':')).encode())
    return {'serializado_bytes':tamano(datos),'checkpoints_bytes':tamano(datos['checkpoints']),
            'deltas_bytes':tamano(datos['registros']),
            'memoria_historia_python_bytes':bytes_estructura(datos)}


def carga(k, acciones=5000):
    e=EstadoPartida('bench','1','1',1,9,'llave',64,JugadorVivo(100,100,10,5,100))
    e.registrar_sala(SalaViva(1,'Sala de referencia sintética'))
    e.conocimiento.explorar(DatosSala(1,'Sala de referencia sintética',()))
    linea=LineaTiempo(e,k)
    for i in range(acciones):
        linea.comenzar()
        e.jugador.vida_actual=50+i%50
        e.jugador.efectos['antorcha']=1+i%100
        e.reloj=i*100+50
        linea.evento()
        e.jugador.vida_actual=max(1,e.jugador.vida_actual-2)
        e.reloj=i*100+100
        linea.evento()
        linea.cerrar_accion({'reloj':i*100},e)
    return linea


def carga_motor(k, acciones=5000):
    """5000 decisiones reales de Sesión, agenda y undo P1; sin servicios externos."""
    from src.orchestrator.bench import _BackendSintetico
    from src.orchestrator.sesion import Sesion
    from src.controller1.fake_provider import CRIPTA_ID
    backend=_BackendSintetico()
    for contenido in backend.fake._contenido.values():
        contenido.enemigos.clear()
        contenido.trampas.clear()
    sesion=Sesion(backend=backend,checkpoint_cada=k)
    sesion.iniciar(CRIPTA_ID,semilla=20261110)
    sesion.estado.jugador.velocidad=100
    sesion.fachada.oleada_cada=10**12
    sesion.fachada.agenda.cancelar_tipo('oleada')
    sesion.fachada._asegurar_oleada()
    for _ in range(acciones):
        ok,mensaje,_=sesion.paso('esperar',grabar=False)
        if not ok: raise AssertionError(mensaje)
    assert len(sesion.linea.acciones)==acciones
    return sesion.linea


def bench_historia(acciones=5000, muestras=1000, calentamientos=100):
    salida={'entorno':{'python':platform.python_version(),'sistema':platform.platform(),'procesador':platform.processor()},
            'acciones':acciones,'muestras':muestras,'calentamientos':calentamientos,
            'carga':'5000 esperar mediante Sesión y motor real; turno jugador, agenda/RNG/undo, tres salas hidratadas; sin enemigos/red/render',
            'resultados':[]}
    referencia=None
    for k in (10,20,50,acciones+1):
        print(f'Historia: K={k}, acciones={acciones}',flush=True,file=sys.stderr)
        linea=carga_motor(k,acciones)
        comprobacion=[linea.consultar(t=i*100+75) for i in range(0,acciones,max(1,acciones//100))]
        if referencia is None: referencia=comprobacion
        else: assert comprobacion==referencia
        indice=[0]
        maximos=[0,0]
        def consulta():
            # Recorrer cortes variados, incluidos puntos intermedios entre eventos.
            i=(indice[0]*173)%acciones
            indice[0]+=1
            resultado=linea.consultar(t=i*100+75)
            maximos[0]=max(maximos[0],linea.ultimas_acciones)
            maximos[1]=max(maximos[1],linea.ultimos_deltas)
            assert linea.ultimas_acciones<=k
            return resultado
        for _ in range(calentamientos): consulta()
        tiempos=[]
        for _ in range(muestras):
            inicio=time.perf_counter_ns();r=consulta();tiempos.append((time.perf_counter_ns()-inicio)/1e6)
            assert 1<=r.vida<=100
        orden=mergesort(tiempos)
        tracemalloc.start();consulta();_,pico=tracemalloc.get_traced_memory();tracemalloc.stop()
        memoria=medir_memoria(linea)
        deltas=len(linea.registros)
        salida['resultados'].append({'k':k,'sin_checkpoints':k>acciones,'mediana_ms':orden[len(orden)//2],
            'p95_ms':orden[(len(orden)*95-1)//100],'max_ms':orden[-1],
            'fallos_50ms':sum(t>50 for t in tiempos),'pico_consulta_bytes':pico,
            **memoria,'deltas':deltas,
            'checkpoints':len(linea.checkpoints),'max_acciones_reconstruidas':maximos[0],'max_deltas_aplicados':maximos[1]})
    return {'historia':salida}
