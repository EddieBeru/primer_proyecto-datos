from config.settings import URL_BASE
import uuid
import requests

from models.errors import ErrorResponse, RateLimitedResponse

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

        response = requests.request(method, url, headers=headers, json=data)
        payload = response.json()
        if model is None:
            return payload
        
        if 'reintentar_en' in payload:
            return RateLimitedResponse.from_dict(payload)
        elif 'error' in payload:
            return ErrorResponse.from_dict(payload)
        
        try:
            return model.from_dict(payload)
        except (KeyError, TypeError, ValueError) as e:
            return ErrorResponse(f"Se recibió una respuesta inesperada: {str(e)}")
       