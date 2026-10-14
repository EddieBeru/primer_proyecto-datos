from src.adapters.session import iniciar_cripta
from src.models.errors import CriptaError, PresupuestoAgotadoError, RateLimitedError
import src.api.endpoints

def rutina_mock():
    print("Iniciando rutina mock...")
    print("Listando criptas:")
    try:
        criptas = src.api.endpoints.listar_criptas()
    except RateLimitedError as e:
        print(f"Servidor ocupado. Reintentar en {e.reintentar_en}s.")
        return
    except CriptaError as e:
        print(f"Error al obtener la lista de criptas: {e}")
        return
    criptas = criptas.criptas
    print(criptas)

    if not criptas:
        print("No se encontraron criptas.")
        return

    primera_cripta_id = criptas[0].id
    print(f"Iniciando sesión de la cripta con ID: {primera_cripta_id}")
    try:
        info, budget = iniciar_cripta(primera_cripta_id)
    except RateLimitedError as e:
        print(f"Servidor ocupado. Reintentar en {e.reintentar_en}s.")
        return
    except CriptaError as e:
        print(f"Error al obtener la información de la cripta: {e}")
        return
    print(info)
    print(f"Presupuesto restante: {budget.get_presupuesto()}")

    try:
        print(f"Obteniendo versión de la cripta con ID: {primera_cripta_id}")
        version = src.api.endpoints.version_cripta(primera_cripta_id, budget)
        print(version)
        print(f"Presupuesto restante: {budget.get_presupuesto()}")
    except PresupuestoAgotadoError as e:
        print(f"Presupuesto agotado: {e}")
        return
    except RateLimitedError as e:
        print(f"Servidor ocupado. Reintentar en {e.reintentar_en}s.")
        return
    except CriptaError as e:
        print(f"Error al obtener la versión de la cripta: {e}")
        return

if __name__ == "__main__":
    rutina_mock()
