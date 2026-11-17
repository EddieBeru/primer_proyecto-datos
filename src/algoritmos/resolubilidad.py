"""Verificación estática incremental; sin HTTP, contenido ni estado de juego."""

import time

from src.estructuras.cola_fifo import ColaFIFO
from src.estructuras.tabla_indice import TablaIndice
from src.models.resolubilidad import ResultadoResolubilidad, UbicacionesLlaves

_DIRS = ("N", "S", "E", "O")


def _primer_ciclo(grafo, candidatos):
    """Tarjan iterativo y un solo retorno por el primer candidato según consulta."""
    n = len(grafo)
    indice = [-1] * n
    bajo = [0] * n
    componente = [-1] * n
    pila_nodos = []
    en_pila = [False] * n
    siguiente_indice = 0
    cantidad_componentes = 0
    for raiz in range(n):
        if indice[raiz] >= 0:
            continue
        marcos = [(raiz, 0, -1)]
        while marcos:
            nodo, pos, padre = marcos[-1]
            if indice[nodo] < 0:
                indice[nodo] = bajo[nodo] = siguiente_indice
                siguiente_indice += 1
                pila_nodos.append(nodo)
                en_pila[nodo] = True
            if pos < len(grafo[nodo]):
                vecino = grafo[nodo][pos][0]
                marcos[-1] = (nodo, pos + 1, padre)
                if indice[vecino] < 0:
                    marcos.append((vecino, 0, nodo))
                elif en_pila[vecino] and indice[vecino] < bajo[nodo]:
                    bajo[nodo] = indice[vecino]
                continue
            marcos.pop()
            if padre >= 0 and bajo[nodo] < bajo[padre]:
                bajo[padre] = bajo[nodo]
            if bajo[nodo] == indice[nodo]:
                while True:
                    miembro = pila_nodos.pop()
                    en_pila[miembro] = False
                    componente[miembro] = cantidad_componentes
                    if miembro == nodo:
                        break
                cantidad_componentes += 1
    tamanos = [0] * cantidad_componentes
    for c in componente:
        tamanos[c] += 1
    cerradas_por_componente = [False] * cantidad_componentes
    for nodo, fila in enumerate(grafo):
        for vecino, evidencia in fila:
            if componente[nodo] == componente[vecino] and evidencia is not None \
                    and evidencia[0] == "puerta":
                cerradas_por_componente[componente[nodo]] = True
    elegido = None
    for nodo in candidatos:
        ciclo = tamanos[componente[nodo]] > 1
        if not ciclo:
            for vecino, _ in grafo[nodo]:
                if vecino == nodo:
                    ciclo = True
                    break
        if ciclo and cerradas_por_componente[componente[nodo]]:
            elegido = nodo
            break
    if elegido is None:
        return (), ()
    # DFS iterativo determinista, conservando si el retorno usa puerta cerrada.
    camino = [elegido]
    aristas = []
    visitado = [False] * (2 * n)
    visitado[2 * elegido] = True
    marcos = [(elegido, 0, False)]
    while marcos:
        nodo, pos, contiene_puerta = marcos[-1]
        if pos >= len(grafo[nodo]):
            marcos.pop()
            if marcos:
                camino.pop()
                aristas.pop()
            continue
        vecino, evidencia = grafo[nodo][pos]
        marcos[-1] = (nodo, pos + 1, contiene_puerta)
        if componente[vecino] != componente[elegido]:
            continue
        tiene_puerta = contiene_puerta or (evidencia is not None and evidencia[0] == "puerta")
        if vecino == elegido and tiene_puerta:
            return tuple(camino + [elegido]), tuple(aristas + [evidencia])
        estado = 2 * vecino + int(tiene_puerta)
        if not visitado[estado]:
            visitado[estado] = True
            camino.append(vecino)
            aristas.append(evidencia)
            marcos.append((vecino, 0, tiene_puerta))
    return (), ()


def verificar_resolubilidad(info, esqueleto, ubicaciones, medir=False):
    """Compila el plano en ordinales compactos y propaga salas/llaves una vez.

    `esqueleto` puede ser un dict de transporte en orden de página o el índice
    neutral del constructor compartido. Toda puerta se valida durante compilación.
    """
    inicio_total = time.perf_counter_ns() if medir else 0
    if not isinstance(ubicaciones, UbicacionesLlaves):
        raise TypeError("ubicaciones debe ser UbicacionesLlaves")
    if ubicaciones.cripta_id != info.id or ubicaciones.version_cripta != info.version:
        raise ValueError("id o versión distinta entre cripta y ubicaciones")
    if not ubicaciones.completa:
        return ResultadoResolubilidad(info.id, info.version, "incompleta",
                                      "consulta de ubicaciones incompleta")
    orden = getattr(esqueleto, "salas_en_orden", ())
    salas = list(orden) if orden else list(esqueleto.values())
    sala_ord = TablaIndice()
    for i, sala in enumerate(salas):
        _, nueva = sala_ord.insertar_si_ausente(sala.id, i)
        if not nueva:
            raise ValueError("sala duplicada")
    if info.sala_inicial not in sala_ord or info.sala_salida not in sala_ord:
        raise ValueError("sala inicial o salida desconocida")
    llaves = TablaIndice()
    ubic_por_sala = [[] for _ in salas]
    ubic_ordinal = []
    for ubic in ubicaciones.llaves:
        sala_ubicacion = sala_ord.obtener(ubic.sala)
        if sala_ubicacion is None:
            raise ValueError(f"ubicación de llave en sala desconocida: {ubic.sala}")
        k, nueva = llaves.insertar_si_ausente(ubic.id, len(ubic_ordinal))
        if nueva:
            ubic_ordinal.append([])
        ubic_ordinal[k].append(ubic)
        ubic_por_sala[sala_ubicacion].append((k, ubic))
    edges = [[] for _ in salas]
    # materializa llaves requeridas y valida puertas, incluso fuera de alcance
    for i, sala in enumerate(salas):
        for direccion in _DIRS:
            salida = sala.salidas.get(direccion)
            if salida is None:
                continue
            destino = sala_ord.obtener(salida.sala)
            if destino is None:
                raise ValueError(f"destino desconocido en sala {sala.id}/{direccion}")
            llave_id = salida.llave
            cerrada = bool(getattr(salida, "cerrada_inicial", salida.cerrada))
            if cerrada and llave_id is None:
                raise ValueError(f"puerta sin llave declarada: sala {sala.id}/{direccion}")
            k = None
            if llave_id is not None:
                k, nueva = llaves.insertar_si_ausente(llave_id, len(ubic_ordinal))
                if nueva:
                    ubic_ordinal.append([])
            edges[i].append((direccion, salida, destino, k, cerrada))
    salida_k, nueva = llaves.insertar_si_ausente(info.llave_salida, len(ubic_ordinal))
    if nueva:
        ubic_ordinal.append([])
    key_count = len(ubic_ordinal)
    obtenida = [False] * key_count
    procesada = [False] * len(salas)
    alcanzable = [False] * len(salas)
    orden_keys = []
    testigo = [None] * len(salas)
    pendientes = [[] for _ in range(key_count)]
    cola = ColaFIFO()
    initial = sala_ord[info.sala_inicial]
    alcanzable[initial] = True
    cola.agregar(initial)

    def obtener(k, ubic):
        if obtenida[k]:
            return
        obtenida[k] = True
        orden_keys.append(k)
        # Solo despierta puertas ya identificadas para esta llave.
        for origen, edge in pendientes[k]:
            descubrir(origen, edge)
        pendientes[k].clear()

    def descubrir(origen, edge):
        direccion, salida, destino, k, cerrada = edge
        if not cerrada or (k is not None and obtenida[k]):
            if not alcanzable[destino]:
                alcanzable[destino] = True
                testigo[destino] = (origen, direccion)
                cola.agregar(destino)
        elif k is not None:
            pendientes[k].append((origen, edge))

    inicio_propagacion = time.perf_counter_ns() if medir else 0
    while not cola.vacia():
        i = cola.sacar()
        if procesada[i]:
            continue
        procesada[i] = True
        # Las llaves locales se obtienen antes de examinar N,S,E,O.
        for k, ubic in ubic_por_sala[i]:
            obtener(k, ubic)
        for edge in edges[i]:
            descubrir(i, edge)
    fin_propagacion = time.perf_counter_ns() if medir else 0

    llave_salida_obtenida = salida_k is not None and obtenida[salida_k]
    destino_final = sala_ord[info.sala_salida]
    puerta_final_declarada = False
    puerta_final_accesible = False
    for i, lista in enumerate(edges):
        for _, _, destino, k, cerrada in lista:
            if destino == destino_final and k == salida_k and salida_k is not None:
                puerta_final_declarada = True
                if alcanzable[i] and (not cerrada or llave_salida_obtenida):
                    puerta_final_accesible = True
    resultado_ok = llave_salida_obtenida and puerta_final_accesible
    no_obtenibles = tuple(ubicaciones.llaves[0].id for _ in ())
    nombres = [None] * key_count
    for clave, ordinal in llaves.items():
        nombres[ordinal] = clave
    no_obtenibles = tuple(nombres[i] for i in range(key_count) if not obtenida[i])
    orden = tuple((nombres[k], ubic_ordinal[k][0] if ubic_ordinal[k] else None)
                  for k in orden_keys)
    frontera = []
    for i, lista in enumerate(edges):
        if not alcanzable[i]:
            continue
        for direccion, _, destino, k, cerrada in lista:
            if cerrada and k is not None and not obtenida[k] and not alcanzable[destino]:
                frontera.append((salas[i].id, direccion, salas[destino].id, nombres[k]))
    # Grafo residual de hechos sala/llave. Cada regla añade como máximo dos
    # incidencias; ubicaciones añaden una. No se forman parejas llave×puerta.
    cantidad_salas = len(salas)
    grafo = [[] for _ in range(cantidad_salas + key_count)]
    alternativas = []
    for origen, lista in enumerate(edges):
        for direccion, _, destino, requerida, cerrada in lista:
            if alcanzable[destino]:
                continue
            if not cerrada:
                if not alcanzable[origen]:
                    grafo[destino].append((origen, None))
            elif requerida is not None and not obtenida[requerida]:
                puerta = ("puerta", salas[origen].id, direccion,
                          salas[destino].id, nombres[requerida])
                alternativas.append(puerta)
                grafo[destino].append((cantidad_salas + requerida, puerta))
                if not alcanzable[origen]:
                    grafo[destino].append((origen, None))
    for k in range(key_count):
        if obtenida[k]:
            continue
        for ubic in ubic_ordinal[k]:
            sala_ubicacion = sala_ord[ubic.sala]
            evidencia = ("ubicacion", nombres[k], ubic.sala, ubic.enemigo)
            grafo[cantidad_salas + k].append((sala_ubicacion, evidencia))
    ciclo_nodos, _ = _primer_ciclo(
        grafo, (cantidad_salas + k for k in range(key_count) if not obtenida[k]))
    ciclo = tuple(nombres[nodo - cantidad_salas] for nodo in ciclo_nodos
                  if nodo >= cantidad_salas)
    if ciclo:
        for k in range(key_count):
            if obtenida[k]:
                continue
            for ubic in ubic_ordinal[k]:
                alternativas.append(("ubicacion", nombres[k], ubic.sala, ubic.enemigo))
    alternativas = tuple(alternativas)
    razones = []
    if not llave_salida_obtenida:
        razones.append(f"no se obtiene la llave de salida {info.llave_salida}")
    if not puerta_final_declarada:
        razones.append(f"no hay puerta que requiera {info.llave_salida} hacia la sala de salida {info.sala_salida}")
    elif not puerta_final_accesible:
        razones.append(f"no se alcanza una puerta que requiera {info.llave_salida} hacia la sala de salida {info.sala_salida}")
    motivo = "; ".join(razones)
    estado = "resoluble" if resultado_ok else "no_resoluble"
    fin_resumen = time.perf_counter_ns() if medir else 0
    tiempos = (("compilacion", inicio_propagacion - inicio_total),
               ("propagacion", fin_propagacion - inicio_propagacion),
               ("resumen", fin_resumen - fin_propagacion)) if medir else ()
    return ResultadoResolubilidad(
        info.id, info.version, estado, motivo, orden, no_obtenibles,
        tuple(frontera), ubicaciones.llaves, ciclo, alternativas,
        (("salas", len(salas)), ("salidas", sum(map(len, edges))),
         ("llaves", key_count), ("ubicaciones", len(ubicaciones.llaves))), tiempos,
    )
