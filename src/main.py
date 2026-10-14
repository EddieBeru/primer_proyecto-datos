import os
import sys
import time

from src.adapters.cli import parse_args
from src.adapters.lru_cache import CacheLRU
from src.adapters.mergesort import mergesort
from src.adapters.room_loader import RoomLoader
from src.adapters.session import iniciar_cripta
from src.models.errors import CriptaError, PresupuestoAgotadoError, RateLimitedError
import src.api.endpoints


def main(argv=None):
    cfg = parse_args(argv)
    if cfg.replay is not None:
        if not os.path.isfile(cfg.replay):
            print(f"Bitácora inexistente: {cfg.replay}")
            return 1
        print(f"--replay {cfg.replay}: pendiente de C2 (el motor reproduce la bitácora).")
        return 0
    if cfg.bench:
        return bench()
    return rutina(cfg)


def bench():
    import random
    rng = random.Random(7)
    print("bench mergesort (tiempos locales, sin red):")
    for n in (500, 2000, 8000):
        datos = [rng.randint(0, n) for _ in range(n)]
        t0 = time.perf_counter()
        mergesort(datos)
        print(f"  n={n}: {time.perf_counter() - t0:.4f}s")
    return 0


def rutina(cfg):
    print("Iniciando rutina mock...")
    print("Listando criptas:")
    try:
        criptas = src.api.endpoints.listar_criptas()
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
        info, budget = iniciar_cripta(primera_cripta_id)
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
        version = src.api.endpoints.version_cripta(primera_cripta_id, budget)
        print(version)

        print("Validando caché del catálogo (Flujo H)...")
        ver_cat = src.api.endpoints.version_catalogo(budget)
        cache = CacheLRU(cfg.cache_size)
        if cache.invalida_si_cambia(ver_cat.version):
            print(f"Caché nueva, versión catálogo: {ver_cat.version}")
        print(f"Presupuesto restante: {budget.get_presupuesto()}")

        print("Descargando esqueleto completo (mapa de salas)...")
        plano = src.api.endpoints.esqueleto_completo(primera_cripta_id, budget, info=info)
        print(f"Salas en el plano: {len(plano)}")
        print(f"Presupuesto restante: {budget.get_presupuesto()}")

        print(f"Cargando sala inicial lista ({info.sala_inicial})...")
        loader = RoomLoader(primera_cripta_id, plano, budget, cache)
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
