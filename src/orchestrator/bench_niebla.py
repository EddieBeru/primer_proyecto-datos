"""Mediciones offline de 002; generación y comprobaciones fuera del cronómetro."""
import platform
import sys
import random
import time
import tracemalloc
from src.algoritmos.rutas import siguiente_paso, ResultadoRuta
from src.controller1.mergesort import mergesort
from src.controller2.conocimiento import MapaConocido
from src.estructuras.tabla_indice import TablaIndice
from src.models.conocimiento import DatosSala, DatosSalida

SEMILLA = 20261106


def medir(fn, muestras=1000):
    calentamientos = min(100, max(1, muestras//10))
    for _ in range(calentamientos):
        fn()
    tiempos = []
    for _ in range(muestras):
        inicio = time.perf_counter_ns()
        fn()
        tiempos.append((time.perf_counter_ns() - inicio) / 1e6)
    orden = mergesort(tiempos)
    tracemalloc.start()
    fn()
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {'mediana_ms': orden[len(orden)//2], 'p95_ms': orden[(len(orden)*95-1)//100],
            'max_ms': orden[-1], 'fallos_5ms': sum(t > 5 for t in tiempos),
            'pico_consulta_bytes': pico, 'muestras': muestras, 'calentamientos': calentamientos}


def crear_mapa(n, forma, parcial=False, desactualizada=False):
    rng = random.Random(SEMILLA)
    mapa = MapaConocido()
    ancho = max(2, int(n ** .5))
    horizontales = [1 if forma == 'empates' else rng.randint(1, 9) for _ in range(n)]
    verticales = [ancho if forma == 'empates' else rng.randint(1, 9) for _ in range(n)]
    for i in range(n):
        arcos = []
        derecha = i+1 < n and (forma == 'cadena' or i % ancho != ancho-1)
        izquierda = i > 0 and (forma == 'cadena' or i % ancho != 0)
        if derecha:
            arcos.append(DatosSalida('E', i+1, horizontales[i], (i, 'E')))
        if forma != 'cadena' and i+ancho < n:
            arcos.append(DatosSalida('S', i+ancho, verticales[i], (i, 'S')))
        if izquierda:
            arcos.append(DatosSalida('O', i-1, horizontales[i-1], (i-1, 'E')))
        if forma != 'cadena' and i >= ancho:
            arcos.append(DatosSalida('N', i-ancho, verticales[i-ancho], (i-ancho, 'S')))
        datos = DatosSala(i, f'Sala {i}', tuple(arcos))
        if not parcial or i < n//2:
            mapa.explorar(datos)
            for salida in arcos:
                mapa.observar(salida.puerta_id, False)
    # Caso desactualizado: se recuerda un cierre, pero la puerta física ya abrió.
    # Este estado de referencia permanece fuera de la adyacencia del jugador.
    mapa.puertas_vivas_bench = tuple((salida.puerta_id, False)
        for sala in mapa.salas() for salida in sala.salidas)
    if desactualizada:
        for i in range(0, n//2 if parcial else n, 7):
            sala = mapa.sala(i)
            if sala and any(s.direccion == 'E' for s in sala.salidas):
                mapa.observar((i, 'E'), True)
    return mapa


def ruta_lineal(origen, destino, adyacentes):
    """Alternativa con cola de prioridad lineal; mismo criterio de relajación."""
    if origen == destino:
        return ResultadoRuta(True, 0)
    etiquetas = TablaIndice()
    etiquetas[origen] = (0, origen, None)
    cola = [(origen, 0, origen, None)]
    while cola:
        minimo = 0
        for i in range(1, len(cola)):
            if (cola[i][1], cola[i][2], cola[i][0]) < (cola[minimo][1], cola[minimo][2], cola[minimo][0]):
                minimo = i
        actual, costo, primero, direccion = cola.pop(minimo)
        if etiquetas.obtener(actual) != (costo, primero, direccion):
            continue
        if actual == destino:
            return ResultadoRuta(True, costo, primero, direccion)
        for salida in adyacentes(actual):
            nuevo = (costo+salida.costo, salida.destino if actual == origen else primero,
                     salida.direccion if actual == origen else direccion)
            previo = etiquetas.obtener(salida.destino)
            if previo is None or nuevo[:2] < previo[:2]:
                etiquetas[salida.destino] = nuevo
                cola.append((salida.destino, *nuevo))
    return ResultadoRuta(False)


def bench_ir_a(tamanos=(100, 1000, 10000), muestras=None):
    resultados = []
    for n in tamanos:
        for forma in ('cadena', 'malla', 'empates'):
            for parcial in (False, True):
                for desactualizada in (False, True):
                    cantidad = muestras if muestras is not None else (1000 if n <= 100 else 100 if n <= 1000 else 10)
                    print(f'002 rutas: V={n} {forma} parcial={parcial} cierres={desactualizada} muestras={cantidad}', file=sys.stderr, flush=True)
                    mapa = crear_mapa(n, forma, parcial, desactualizada)
                    destino = n//2-1 if parcial else n-1
                    heap = lambda: siguiente_paso(0, destino, mapa.adyacentes)
                    lineal = lambda: ruta_lineal(0, destino, mapa.adyacentes)
                    assert heap() == lineal()
                    resultados.append({'V': n, 'forma': forma, 'parcial': parcial,
                        'recuerdo_con_cierres': desactualizada,
                        'V_conocido': len(mapa._salas),
                        'E_conocido': sum(len(s.salidas) for s in mapa.salas()),
                        'heap': medir(heap, cantidad), 'cola_lineal': medir(lineal, cantidad)})
    return {'niebla_rutas': resultados}


class IndiceContado(TablaIndice):
    def __init__(self):
        super().__init__()
        self.consultas = self.escrituras = self.rehash_registros = self.expansiones = 0
    def _buscar(self, clave):
        self.consultas += 1
        return super()._buscar(clave)
    def __setitem__(self, clave, valor):
        self.escrituras += 1
        super().__setitem__(clave, valor)
    def _expandir(self):
        self.expansiones += 1
        self.rehash_registros += len(self)
        super()._expandir()


def bench_conocimiento(tamanos=(100, 1000, 10000), muestras=None):
    resultados = []
    for n in tamanos:
        cantidad = muestras if muestras is not None else (1000 if n <= 100 else 100 if n <= 1000 else 10)
        print(f'002 conocimiento: V={n} muestras={cantidad}', file=sys.stderr, flush=True)
        mapa = crear_mapa(n, 'malla')
        registros = list(mapa.salas())
        destino = n-1
        indice = lambda: mapa.sala(destino)
        lineal = lambda: next(s for s in registros if s.id == destino)
        assert indice() == lineal()
        fila = {'V': n, 'indice': medir(indice, cantidad), 'lineal': medir(lineal, cantidad),
                'mapa_completo': medir(lambda: mergesort(mapa.a_dict()['salas'], clave=lambda s: s['id']), cantidad)}
        # Mismas dos salas nuevas, sin atravesar capacidad: contar accesos, no tiempo solamente.
        contado = IndiceContado()
        for s in registros:
            contado[s.id] = s
        mapa._salas = contado
        antes = (contado.consultas, contado.escrituras, contado.rehash_registros)
        datos = DatosSala(n+1, 'Nueva', (DatosSalida('E', n+2, 1, (n+1, 'E')),))
        mapa.explorar(datos)
        fila['revelacion'] = {'consultas': contado.consultas-antes[0],
            'escrituras': contado.escrituras-antes[1], 'rehash_registros': contado.rehash_registros-antes[2]}
        # Secuencia completa incluye cada expansión y todos sus registros recorridos.
        indice_nuevo = IndiceContado()
        inicio = time.perf_counter_ns()
        for i in range(n):
            indice_nuevo[i] = i
        fila['secuencia_expansiones'] = {'ms': (time.perf_counter_ns()-inicio)/1e6,
            'altas': n, 'expansiones': indice_nuevo.expansiones,
            'rehash_registros': indice_nuevo.rehash_registros}
        resultados.append(fila)
    return {'niebla_entorno': {'semilla': SEMILLA, 'python': platform.python_version(),
        'sistema': platform.platform(), 'cpu': platform.processor() or platform.machine()}, 'niebla_conocimiento': resultados}
