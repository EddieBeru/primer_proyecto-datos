class CriptaError(Exception):
    pass


class BadRequestError(CriptaError):
    """400: petición mal formada. Error nuestro, no reintentar."""

    pass


class NotFoundError(CriptaError):
    """404: recurso no existe. No reintentar."""

    pass


class ServerError(CriptaError):
    """500: contenido inválido del servidor. No insistir sin fin."""

    pass


class NetworkError(CriptaError):
    """Sin conexión, timeout u otro fallo de transporte."""

    pass


class UnexpectedResponseError(CriptaError):
    """Respuesta 200 pero con forma inesperada (from_dict falla)."""

    pass


class RateLimitedError(CriptaError):
    """429: servidor pide esperar. Trae segundos para reintentar."""

    def __init__(self, message: str, reintentar_en: int):
        super().__init__(message)
        self.reintentar_en = reintentar_en


class PresupuestoAgotadoError(CriptaError):
    """Presupuesto de solicitudes agotado. Decisión equipo pendiente (K4)."""

    pass


class BitacoraError(CriptaError):
    """Bitácora ilegible o línea corrupta. No insistir, avisar."""

    pass
