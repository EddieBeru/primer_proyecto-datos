from src.models.errors import CriptaError, RateLimitedError
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
    
    if criptas and len(criptas) > 0:
        primera_cripta_id = criptas[0].id
        print(f"Obteniendo información de la cripta con ID: {primera_cripta_id}")
        info = src.api.endpoints.info_cripta(primera_cripta_id)
        print(info)
        
        print(f"Obteniendo versión de la cripta con ID: {primera_cripta_id}")
        version = src.api.endpoints.version_cripta(primera_cripta_id)
        print(version)
    else:
        print("No se encontraron criptas.")

if __name__ == "__main__":
    rutina_mock()