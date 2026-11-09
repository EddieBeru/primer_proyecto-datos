"""Control transitorio de viaje, sin ruta persistida ni acceso al grafo vivo."""

from dataclasses import dataclass
from src.algoritmos.rutas import siguiente_paso


@dataclass
class ContextoPaso:
    recibio_dano: bool = False
    enemigos_vivos_al_entrar: bool = False
    movimiento_realizado: bool = False
    error: str | None = None
    motivo: str | None = None


@dataclass
class ControlViaje:
    destino: int | None = None
    activo: bool = False
    ultimo_motivo: str | None = None

    def detener(self, motivo):
        self.activo = False
        self.ultimo_motivo = motivo

    def iniciar(self, estado, destino):
        self.detener("cancelado")
        sala = estado.conocimiento.sala(destino) if type(destino) is int else None
        if sala is None or sala.estado != "explorada":
            return False, "El destino debe ser una sala explorada."
        self.destino = destino
        if destino == estado.sala_actual:
            self.detener("destino")
            return True, "Ya estás en el destino."
        if estado.estado != "jugando":
            self.detener("fin_partida")
            return False, "La partida terminó."
        if any(e.vivo for e in estado.sala_en_curso().enemigos):
            self.detener("enemigos")
            return False, "Hay enemigos vivos en la sala de partida."
        self.activo, self.ultimo_motivo = True, None
        return True, "Viaje iniciado."

    def ruta(self, estado):
        return siguiente_paso(estado.sala_actual, self.destino, estado.conocimiento.adyacentes)

    def finalizar(self, estado, contexto):
        if estado.estado != "jugando":
            motivo = "fin_partida"
        elif contexto.recibio_dano:
            motivo = "dano"
        elif contexto.enemigos_vivos_al_entrar or any(e.vivo for e in estado.sala_en_curso().enemigos):
            motivo = "enemigos"
        elif estado.sala_actual == self.destino:
            motivo = "destino"
        elif not self.activo:
            motivo = self.ultimo_motivo or "cancelado"
        elif contexto.error:
            motivo = "error"
        elif not self.ruta(estado).alcanzable:
            motivo = "sin_ruta"
        else:
            return
        contexto.motivo = motivo
        self.detener(motivo)
