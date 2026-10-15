import os
import sys

from src.controller1.cli import parse_args
from src.controller1.lru_cache import CacheLRU
from src.controller1.room_loader import RoomLoader
from src.controller1.session import iniciar_cripta, listar_criptas
from src.models.errors import CriptaError, PresupuestoAgotadoError, RateLimitedError
import src.controller1.endpoints as endpoints


def main(argv=None):
    cfg = parse_args(argv)
    if cfg.replay is not None:
        return modo_replay(cfg)
    if cfg.bench:
        return modo_bench()
    if cfg.vista:
        return modo_vista(cfg)
    if cfg.jugar:
        return modo_jugar(cfg)
    return rutina(cfg)


def modo_bench():
    from src.orchestrator.bench import correr_todo
    res = correr_todo()
    print("bench por subsistema (sin red, sin vista):")
    for k in sorted(res):
        v = res[k]
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")
    return 0


def modo_replay(cfg):
    """--replay vía Sesión: valida header, reconstruye (red/offline) y re-ejecuta."""
    from src.controller2.bitacora import BitacoraIncompatibleError
    from src.orchestrator.sesion import Sesion
    if not os.path.isfile(cfg.replay):
        print(f"Bitácora inexistente: {cfg.replay}")
        return 1
    ses = _nueva_sesion(cfg, log_ruta=None)
    try:
        foto = ses.reproducir(cfg.replay)
    except BitacoraIncompatibleError as e:
        print(str(e))
        return 1
    except CriptaError as e:
        print(f"No se pudo reproducir: {e}")
        return 1
    print(f"replay ok: sala {foto.sala_id} estado {foto.estado}")
    return 0


def _nueva_sesion(cfg, log_ruta="partida.log"):
    from src.orchestrator.sesion import Sesion
    backend = endpoints
    if cfg.offline:
        from src.controller1.offline import OfflineBackend
        backend = OfflineBackend(cfg.offline)
        print(f"Modo offline: {cfg.offline} (no cuenta red)")
    return Sesion(backend=backend, cache_size=cfg.cache_size, jugador=cfg.jugador,
                  log_ruta=log_ruta)


def modo_vista(cfg):
    """Partida gráfica Pygame vía Sesión (la vista solo habla con Sesión)."""
    import pygame

    from src.view.app import VistaApp, rutas_log_por_defecto
    pygame.init()
    ses = _nueva_sesion(cfg, log_ruta=None)
    if cfg.cargar:
        try:
            foto = ses.cargar_en_frio(cfg.cargar)
            print(f"Partida cargada de {cfg.cargar}.")
        except CriptaError as e:
            print(f"No se pudo cargar: {e}")
            return 1
    else:
        try:
            criptas = ses.backend.listar_criptas()
        except CriptaError as e:
            print(f"Error al listar criptas: {e}")
            return 1
        ids = [c.id for c in criptas.criptas]
        if not ids:
            print("No se encontraron criptas.")
            return 1
        log_ruta, _bin_ruta = rutas_log_por_defecto()
        ses = _nueva_sesion(cfg, log_ruta=log_ruta)
        foto = None
    dev = os.environ.get("CRIPTA_DEV") == "1"
    app = VistaApp(ses, dev=dev,
                   save_path=cfg.guardar or rutas_log_por_defecto()[1])
    if foto is not None:
        app.foto = foto
        app.pantalla = "juego"
    else:
        tarjetas = [
            {"id": c.id, "nombre": getattr(c, "nombre", c.id),
             "salas": getattr(c, "salas", "?"),
             "dificultad": getattr(c, "dificultad", "?")}
            for c in criptas.criptas
        ]
        app.listar_para_seleccion(tarjetas, os.path.isfile(app.save_path))
        if len(tarjetas) == 1:
            try:
                app.iniciar_partida(str(tarjetas[0]["id"]), semilla=cfg.semilla)
            except CriptaError as e:
                print(f"Error al iniciar: {e}")
                return 1
    return app.ejecutar()


def modo_jugar(cfg):
    """Partida interactiva en consola vía Sesión (la Vista hará lo mismo)."""
    from src.orchestrator.consola import bucle, renderizar
    ses = _nueva_sesion(cfg)
    try:
        if cfg.cargar:
            foto = ses.cargar_en_frio(cfg.cargar)
            print(f"Partida cargada de {cfg.cargar}.")
            renderizar(foto)
        else:
            criptas = ses.backend.listar_criptas()
            ids = [c.id for c in criptas.criptas]
            if not ids:
                print("No se encontraron criptas.")
                return 1
            print(f"Criptas: {ids}")
            foto = ses.iniciar(ids[0], semilla=cfg.semilla)
            print(f"Cripta {ids[0]}, semilla {cfg.semilla}.")
    except RateLimitedError as e:
        print(f"Servidor ocupado. Reintentar en {e.reintentar_en}s.")
        return 1
    except CriptaError as e:
        print(f"Error al iniciar: {e}")
        return 1
    if cfg.guardar:
        try:
            ses.guardar(cfg.guardar)
            print(f"Guardado inicial en {cfg.guardar}.")
            return 0
        except CriptaError as e:
            print(f"No se pudo guardar: {e}")
            return 1
    return bucle(ses)


def rutina(cfg):
    backend = endpoints
    if cfg.offline:
        from src.controller1.offline import OfflineBackend
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
            from src.controller1.budget import BudgetAdapter
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
