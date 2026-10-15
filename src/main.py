import os
import sys

from src.adapters.cli import parse_args
from src.adapters.lru_cache import CacheLRU
from src.adapters.room_loader import RoomLoader
from src.adapters.session import iniciar_cripta, listar_criptas
from src.models.errors import CriptaError, PresupuestoAgotadoError, RateLimitedError
import src.api.endpoints as endpoints


def main(argv=None):
    cfg = parse_args(argv)
    if cfg.replay is not None:
        return modo_replay(cfg)
    if cfg.bench:
        return modo_bench()
    return rutina(cfg)


def modo_bench():
    from src.adapters.bench import correr_todo
    res = correr_todo()
    print("bench por subsistema (sin red, sin vista):")
    for k in sorted(res):
        v = res[k]
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")
    return 0


def modo_replay(cfg):
    from src.adapters.gamelog import Bitacora
    from src.controller import EstadoPartida, Fachada, reproducir
    from src.controller.bitacora import BitacoraIncompatibleError, parsear_header
    if not os.path.isfile(cfg.replay):
        print(f"Bitácora inexistente: {cfg.replay}")
        return 1
    try:
        lineas = Bitacora(cfg.replay).leer()
    except CriptaError as e:
        print(f"Bitácora ilegible: {e}")
        return 1
    if not lineas or not lineas[0].startswith("#cripta"):
        print("Replay sin header #cripta: no se puede validar versión.")
        return 1
    try:
        head = parsear_header(lineas[0])
    except ValueError as e:
        print(f"Header inválido: {e}")
        return 1
    # Estado mínimo compatible para validar: se reconstruye al cargar partida.
    print(f"--replay {cfg.replay}: {head['cripta_id']} {head['version_cripta']} semilla {head['semilla']}")
    if cfg.cargar:
        from src.adapters import savegame
        try:
            data = savegame.cargar(cfg.cargar)
        except CriptaError as e:
            print(f"No se pudo cargar: {e}")
            return 1
        est = EstadoPartida.desde_dict(data)
    else:
        print("Replay necesita --cargar <partida.bin> o red para el estado inicial.")
        return 1
    fac = Fachada(est, _ProveedorVacio(), {}, Bitacora(cfg.replay), semilla=head["semilla"])
    try:
        reproducir(fac, lineas)
    except BitacoraIncompatibleError as e:
        print(str(e))
        return 1
    f = fac.foto()
    print(f"replay ok: sala {f.sala_id} estado {f.estado} acciones {est.acciones_jugador}")
    return 0


class _ProveedorVacio:
    def sala_lista(self, n):
        raise CriptaError(f"replay sin red: sala {n} debe estar cargada")


def rutina(cfg):
    backend = endpoints
    if cfg.offline:
        from src.adapters.offline import OfflineBackend
        backend = OfflineBackend(cfg.offline)
        print(f"Modo offline: {cfg.offline} (no cuenta red)")
    print("Listando criptas:")
    try:
        criptas = listar_criptas() if backend is endpoints else backend.listar_criptas()
    except RateLimitedError as e:
        print(f"Servidor ocupado. Reintentar en {e.reintentar_en}s.")
        return 1
    except CriptaError as e:
        print(f"Error al obtener la lista de criptas: {e}")
        return 1
    criptas = criptas.criptas
    print(criptas)
    if not criptas:
        print("No se encontraron criptas.")
        return 1

    primera_cripta_id = criptas[0].id
    print(f"Iniciando sesión de la cripta con ID: {primera_cripta_id}")
    try:
        if backend is endpoints:
            info, budget = iniciar_cripta(primera_cripta_id)
        else:
            info = backend.info_cripta(primera_cripta_id)
            from src.adapters.budget import BudgetAdapter
            budget = BudgetAdapter(info.presupuesto_solicitudes)
    except RateLimitedError as e:
        print(f"Servidor ocupado. Reintentar en {e.reintentar_en}s.")
        return 1
    except CriptaError as e:
        print(f"Error al obtener la información de la cripta: {e}")
        return 1
    print(info)
    print(f"Presupuesto restante: {budget.get_presupuesto()}")

    try:
        print(f"Obteniendo versión de la cripta con ID: {primera_cripta_id}")
        version = backend.version_cripta(primera_cripta_id, budget)
        print(version)

        print("Validando caché del catálogo (Flujo H)...")
        ver_cat = backend.version_catalogo(budget)
        cache = CacheLRU(cfg.cache_size)
        if cache.invalida_si_cambia(ver_cat.version):
            print(f"Caché nueva, versión catálogo: {ver_cat.version}")
        print(f"Presupuesto restante: {budget.get_presupuesto()}")

        print("Descargando esqueleto completo (mapa de salas)...")
        if hasattr(backend, "esqueleto_completo"):
            plano = backend.esqueleto_completo(primera_cripta_id, budget, info=info)
        else:
            plano = endpoints.esqueleto_completo(primera_cripta_id, budget, info=info)
        print(f"Salas en el plano: {len(plano)}")
        print(f"Presupuesto restante: {budget.get_presupuesto()}")

        print(f"Cargando sala inicial lista ({info.sala_inicial})...")
        loader = RoomLoader(primera_cripta_id, plano, budget, cache, backend=backend)
        sala = loader.sala_lista(info.sala_inicial)
        print(f"Sala {sala.room.id} ({sala.room.nombre})")
        for e in sala.enemigos:
            print(f"  enemigo {e.instancia}: {e.ficha.id} vida {e.vida_actual}")
        for o in sala.objetos:
            print(f"  objeto: {o.ficha.id}")
        for t in sala.trampas:
            print(f"  trampa {t.instancia}: {t.ficha.id}")
        print(f"Fichas en caché: {len(cache)} (tope {cfg.cache_size})")
        print(f"Presupuesto restante: {budget.get_presupuesto()}")
        rep = budget.reporte()
        print(f"Reporte red: realizadas={rep['realizadas']} presupuesto={rep['presupuesto']} "
              f"hits={rep['hits']} misses={rep['misses']}")
    except PresupuestoAgotadoError as e:
        print(f"Presupuesto agotado: {e}")
        return 1
    except RateLimitedError as e:
        print(f"Servidor ocupado. Reintentar en {e.reintentar_en}s.")
        return 1
    except CriptaError as e:
        print(f"Error en la rutina: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
