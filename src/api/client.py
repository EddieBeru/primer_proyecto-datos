from config.settings import URL_BASE
import uuid
import requests

from src.models.errors import (
    BadRequestError,
    CriptaError,
    NetworkError,
    NotFoundError,
    RateLimitedError,
    ServerError,
    UnexpectedResponseError,
)

class Client:
    _instance = None
    url_base = None
    uuid = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.url_base = URL_BASE
            cls._instance.uuid = str(uuid.uuid4())
        return cls._instance

    # Función generica para hacer oslicitudes a la API manejando el UUID y los errores según pide la documentación.
    def make_request(
            self, 
            endpoint, 
            method='GET', 
            data=None,
            model = None 
            ):
        url = f"{self.url_base}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'X-Cripta-Client-Id': self.uuid
        }

        try:
            response = requests.request(method, url, headers=headers, json=data)
        except requests.RequestException as e:
            raise NetworkError(f"Fallo de red: {str(e)}") from e

        try:
            payload = response.json()
        except ValueError as e:
            raise UnexpectedResponseError(f"Respuesta no JSON: {str(e)}") from e

        if response.status_code == 429:
            raise RateLimitedError(
                payload.get("error", "Servidor ocupado") if isinstance(payload, dict) else "Servidor ocupado",
                payload.get("reintentar_en", 1) if isinstance(payload, dict) else 1,
            )
        elif response.status_code == 400:
            raise BadRequestError(payload.get("error", "Petición mal formada") if isinstance(payload, dict) else "Petición mal formada")
        elif response.status_code == 404:
            raise NotFoundError(payload.get("error", "Recurso no encontrado") if isinstance(payload, dict) else "Recurso no encontrado")
        elif response.status_code == 500:
            raise ServerError(payload.get("error", "Error interno del servidor") if isinstance(payload, dict) else "Error interno del servidor")
        elif response.status_code >= 400:
            raise CriptaError(payload.get("error", f"HTTP {response.status_code}") if isinstance(payload, dict) else f"HTTP {response.status_code}")

        if model is None:
            return payload

        try:
            return model.from_dict(payload)
        except (KeyError, TypeError, ValueError) as e:
            raise UnexpectedResponseError(f"Se recibió una respuesta inesperada: {str(e)}") from e
       