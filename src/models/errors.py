from dataclasses import dataclass

@dataclass
class ErrorResponse:
    error: str

    @classmethod
    def from_dict(cls, data: dict) -> "ErrorResponse":
        return cls(
            error=data["error"],
        )

@dataclass
class RateLimitedResponse:
    error: str
    reintentar_en: int  # >= 1

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitedResponse":
        return cls(
            error=data["error"],
            reintentar_en=data["reintentar_en"],
        )