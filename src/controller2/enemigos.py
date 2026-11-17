"""Comportamiento de enemigos y rastro (§2.8/§2.9 doc oficial).

Si comparte sala con jugador: ataca (lo decide la fachada), no se mueve.
Si no: guardián espera, errante azar entre abiertas, rastreador vecina
abierta con rastro más fresco <400 (empate menor id).
Costo mover/atacar/esperar = 100 siempre.
"""

from __future__ import annotations

from src.controller2.agenda import Agenda
from src.controller2.efectos import REGENERACION_PERIODO
from src.controller2.modelo import EnemigoInstancia, EstadoPartida, SalaViva
from src.controller2.orden_local import insercion
from src.controller2.reloj import RelojVirtual

COMPORTAMIENTOS = ("guardián", "errante", "rastreador", "cazador")
RASTRO_MAX_ANTIGUEDAD = 400
OLEADA_CADA = 3000  # una aparición cada N unidades virtuales (default)
OLEADA_MAX = 4  # tope de aparecidos vivos a la vez
PREFIJO_OLEADA = "oleada-"


def comportamiento_de(catalogo: dict | None, tipo_id: str) -> str:
    ficha = (catalogo or {}).get(tipo_id)
    comp = getattr(ficha, "comportamiento", "guardián")
    return comp if comp in COMPORTAMIENTOS else "guardián"


def velocidad_de(catalogo: dict | None, tipo_id: str, defecto: int = 5) -> int:
    ficha = (catalogo or {}).get(tipo_id)
    vel = int(getattr(ficha, "velocidad", defecto) or defecto)
    return vel if vel > 0 else defecto


def regeneracion_de(catalogo: dict | None, tipo_id: str) -> int | None:
    """Curación por pulso si la ficha la declara (§2.10); None si no."""
    ficha = (catalogo or {}).get(tipo_id)
    valor = getattr(ficha, "regeneracion", None)
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _vecinas_abiertas(estado: EstadoPartida, sala_id: int) -> list[int]:
    sala = estado.salas.get(sala_id)
    if sala is None:
        return []
    out = []
    for salida in sala.salidas.values():
        if salida.cerrada:
            continue
        if salida.destino in estado.salas and salida.destino not in out:
            out.append(salida.destino)
    return insercion(out)


def _sala_de(estado: EstadoPartida, instancia_id: str):
    for sala in estado.salas.values():
        for e in sala.enemigos:
            if e.instancia == instancia_id and e.vivo:
                return sala, e
    return None, None


def activar_sala(estado: EstadoPartida, agenda: Agenda, ahora: int,
                 sala_id: int, catalogo: dict | None = None) -> list:
    """Activa dormidos de sala (§2.4): costo 100 desde ahora, orden instancia."""
    sala = estado.salas.get(sala_id)
    if sala is None:
        return []
    dormidos = insercion(
        [e for e in sala.enemigos if e.vivo and not e.activa],
        clave=lambda e: e.instancia,
    )
    evs = []
    for e in dormidos:
        e.activa = True
        vel = velocidad_de(catalogo, e.tipo_id)
        from src.controller2.reloj import intervalo
        ev = agenda.programar(ahora + intervalo(100, vel), "turno",
                              {"actor": e.instancia, "kind": "enemigo",
                               "tipo": e.tipo_id, "costo": 100})
        e.tiempo_siguiente = ev.t
        evs.append(ev)
        # §2.10: un enemigo que declare regeneración pulsa cada 200.
        cant = regeneracion_de(catalogo, e.tipo_id)
        if cant:
            evs.append(agenda.programar(
                ahora + REGENERACION_PERIODO, "regeneracion",
                {"instancia": e.instancia, "cantidad": cant}))
    return evs


def decidir_accion_cazador(
    estado: EstadoPartida,
    instancia_id: str,
    catalogo: dict | None = None,
    proveedor: Any = None,
    distancias_destino: Any = None,
    ubicacion=None,
) -> tuple[str, int, int | None]:
    """Evalúa la acción del cazador según el orden estricto de prioridades (FR-CAZ-05):
    1. Si comparte la sala con el jugador al inicio de su turno: ataca cuerpo a cuerpo ("atacar", 100, None).
    2. Si no comparte sala: calcula la ruta de costo mínimo d hacia el jugador a través de salidas abiertas.
    3. Si no existe ruta abierta o d > rango: espera en su sala ("esperar", 100, None).
    4. Si d <= rango: avanza un paso por la ruta óptima ("mover", costo_salida, siguiente_sala).
    """
    sala, actual = ubicacion if ubicacion is not None else _sala_de(estado, instancia_id)
    if actual is None or sala is None:
        return "esperar", 100, None

    # Prioridad 1: Atacar cuerpo a cuerpo si comparte sala con el jugador
    if sala.id == estado.sala_actual:
        return "atacar", 100, None

    ficha = (catalogo or {}).get(actual.tipo_id)
    rango = int(getattr(ficha, "rango", 0) or 0)
    if rango < 1:
        return "esperar", 100, None

    # Verificar caché de ruta si existe (invalidación instantánea O(1) si cambiaron puertas o jugador)
    cache: Any = getattr(actual, "_ruta_cazador", None)
    if cache is not None and cache.es_valida(estado, sala.id):
        sig = cache.siguiente_sala
        salida_cache = next((s for s in sala.salidas.values() if s.destino == sig and not s.cerrada), None)
        if salida_cache is not None:
            return "mover", int(getattr(salida_cache, "costo", 100)), sig

    from src.controller2.rutas import dijkstra_acotado, RutaCazador

    d, siguiente = dijkstra_acotado(
        estado=estado,
        origen=sala.id,
        destino=estado.sala_actual,
        rango_max=rango,
        distancias_destino=distancias_destino,
        proveedor=proveedor,
    )

    if d is None or siguiente is None or d > rango:
        actual._ruta_cazador = None
        return "esperar", 100, None

    salida_opt = next((s for s in sala.salidas.values() if s.destino == siguiente and not s.cerrada), None)
    if salida_opt is None:
        actual._ruta_cazador = None
        return "esperar", 100, None

    costo_paso = int(getattr(salida_opt, "costo", 100))
    actual._ruta_cazador = RutaCazador(
        cazador_id=instancia_id,
        sala_cazador=sala.id,
        sala_jugador=estado.sala_actual,
        puertas_version=getattr(estado, "puertas_version", 0),
        costo_total=d,
        siguiente_sala=siguiente,
    )
    return "mover", costo_paso, siguiente


def decidir_destino(estado: EstadoPartida, instancia_id: str,
                    catalogo: dict | None = None, ahora: int = 0,
                    azar=None) -> int | None:
    """Sala destino o None (quedarse). Errante usa azar reproducible."""
    sala, actual = _sala_de(estado, instancia_id)
    if actual is None or sala is None:
        return None
    # Si comparte sala con jugador: ataca, no se mueve (§2.8).
    if sala.id == estado.sala_actual:
        return None
    comp = comportamiento_de(catalogo, actual.tipo_id)
    if comp == "cazador":
        _accion, _costo, destino = decidir_accion_cazador(estado, instancia_id, catalogo)
        return destino
    vecinas = _vecinas_abiertas(estado, actual.sala_actual)
    if comp == "guardián" or not vecinas:
        return None
    if comp == "rastreador":
        mejor = None
        mejor_t = None
        for v in vecinas:
            visita = estado.salas[v].ultima_visita
            if visita is None:
                continue
            if ahora - int(visita) >= RASTRO_MAX_ANTIGUEDAD:
                continue
            if mejor is None or int(visita) > int(mejor_t) or (
                int(visita) == int(mejor_t) and v < mejor
            ):
                mejor, mejor_t = v, visita
        return mejor
    # Errante: azar entre abiertas (§2.8). Sin azar inyectado: primera (tests).
    if azar is None:
        return vecinas[0]
    try:
        estado.azar_llamadas = int(getattr(estado, "azar_llamadas", 0)) + 1
    except Exception:
        pass
    return azar.choice(vecinas)  # ya vienen ordenadas por _vecinas_abiertas


def mover_enemigo(estado: EstadoPartida, instancia_id: str, destino: int, ubicacion=None) -> bool:
    """Mueve la instancia entre salas usando la ubicación resuelta en su turno."""
    origen, objetivo = ubicacion if ubicacion is not None else _sala_de(estado, instancia_id)
    if objetivo is None or destino not in estado.salas:
        return False
    if origen is not None and origen.id != destino:
        origen.enemigos = [e for e in origen.enemigos if e.instancia != instancia_id]
        objetivo.sala_actual = destino
        estado.salas[destino].enemigos.append(objetivo)
    return True


def decaer_rastro(estado: EstadoPartida, cantidad: int = 1) -> None:
    """Compat: ya no se usa (rastro es timestamp). Solo para tests viejos."""
    return None


def tabla_oleada(catalogo: dict | None) -> list[str]:
    """Tipos spawnables: errantes si hay (se mueven random), si no cualquiera."""
    fichas = [fid for fid, f in (catalogo or {}).items()
              if getattr(f, "clase", "") == "enemigo"]
    errantes = [fid for fid in fichas
                if comportamiento_de(catalogo, fid) == "errante"]
    return errantes or fichas


def vivos_oleada(estado: EstadoPartida) -> int:
    """Aparecidos vivos (tope anti-inundación)."""
    return sum(1 for s in estado.salas.values() for e in s.enemigos
               if e.vivo and e.instancia.startswith(PREFIJO_OLEADA))


def programar_oleada(agenda: Agenda, reloj: RelojVirtual,
                     cada: int = OLEADA_CADA):
    """Agenda la próxima aparición. Datos mínimos (serializable K2)."""
    return agenda.programar(reloj.ahora + int(cada), "oleada", {"cada": int(cada)})


def ejecutar_oleada(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                    catalogo: dict | None, azar=None,
                    seq: int = 0) -> tuple[str | None, int | None]:
    """Aparece un errante en la sala actual. Determinista (azar+seq).

    Retorna (instancia, seq_turno) o (None, None) si toca saltar (tope,
    sin pool o sala desconocida). Quien llama reprograma la siguiente.
    """
    pool = tabla_oleada(catalogo)
    sala = estado.salas.get(estado.sala_actual)
    if not pool or sala is None or vivos_oleada(estado) >= OLEADA_MAX:
        return None, None
    tipo = pool[azar.randint(0, len(pool) - 1)] if azar is not None else pool[0]
    ficha = (catalogo or {}).get(tipo)
    vida = int(getattr(ficha, "vida_max", 10) or 10)
    inst = f"{PREFIJO_OLEADA}{int(seq)}"
    enemigo = EnemigoInstancia(inst, tipo, vida, sala.id, activa=True)
    sala.enemigos.append(enemigo)
    ev = reloj.programar_turno(agenda, inst, velocidad_de(catalogo, tipo),
                               {"kind": "enemigo", "tipo": tipo}, costo=100)
    enemigo.tiempo_siguiente = ev.t
    return inst, ev.seq


def turno_enemigo(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                  instancia_id: str, catalogo: dict | None = None,
                  azar=None, proveedor=None, ubicacion=None, distancias_destino=None) -> str:
    """Ejecuta un turno: decide, mueve y reprograma el siguiente."""
    origen_sala, actor = ubicacion if ubicacion is not None else _sala_de(estado, instancia_id)
    costo_accion = 100
    tipo_inicial = actor.tipo_id if actor is not None else None
    if comportamiento_de(catalogo, tipo_inicial) == "cazador":
        _, costo_accion, destino = decidir_accion_cazador(
            estado, instancia_id, catalogo, proveedor=proveedor,
            ubicacion=(origen_sala, actor), distancias_destino=distancias_destino)
    else:
        destino = decidir_destino(estado, instancia_id, catalogo, reloj.ahora, azar)
    if destino is not None and origen_sala is not None:
        salida_usada = next((s for s in origen_sala.salidas.values() if s.destino == destino), None)
        if salida_usada is not None:
            costo_accion = int(getattr(salida_usada, "costo", 100))
        if destino not in estado.salas and proveedor is not None:
            from src.controller2.rutas import _obtener_salidas_sala
            datos = proveedor.datos_sala(destino)
            salidas = _obtener_salidas_sala(estado, destino, proveedor)
            estado.salas[destino] = SalaViva(
                datos.id, datos.nombre,
                salidas={s.direccion: s for s in salidas},
                contenido_pendiente=True)
        mover_enemigo(estado, instancia_id, destino, ubicacion=(origen_sala, actor))
    tipo = tipo_inicial
    if tipo is not None:
        ev = reloj.programar_turno(agenda, instancia_id, velocidad_de(catalogo, tipo),
                                   {"kind": "enemigo", "tipo": tipo}, costo=costo_accion)
        actor.tiempo_siguiente = ev.t
    return f"{instancia_id}->" + (str(destino) if destino is not None else "quieto")
