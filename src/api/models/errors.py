from dataclasses import dataclass

@dataclass
class ErrorResponse:
    error: str

@dataclass
class RateLimitedResponse:
    error: str
    reintentar_en: int  # >= 1