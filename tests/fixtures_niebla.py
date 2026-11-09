"""Datos sintéticos de002, sin HTTP ni dependencia de la entrega ponderada001.

El falso separa metadatos, contenido y activaciones. ``solo_metadatos`` falla
ante cualquier acceso de contenido/fichas o activación durante revelación/ruta.
Las salidas vivas ponderadas son exclusivamente de prueba; no cambian K1 vigente.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

import pytest

from src.controller2.modelo import (
    EnemigoInstancia, JugadorVivo, SalaViva, SalidaViva, TrampaInstancia,
)
from src.estructuras.tabla_indice import TablaIndice
from src.models.catalog import Enemy, Trap
from src.models.conocimiento import DatosSala, DatosSalida
from src.models.errors import NotFoundError
from src.models.objects import Key, Potion, RewindScroll, Torch

INICIO = 2
VECINA = 5
LEJANA = 10**12
AISLADA = 999


@dataclass
class SalidaPonderadaFalsa(SalidaViva):
    costo: int = 100


class ProveedorNiebla:
    def precargar_vecinas(self, sala_id):
        pass  # Las salas de la fixture ya están disponibles, sin revelar.

    def __init__(self, metadatos: tuple[DatosSala, ...], salas: tuple[SalaViva, ...]):
        self._metadatos: TablaIndice[DatosSala] = TablaIndice()
        self._salas: TablaIndice[SalaViva] = TablaIndice()
        for datos in metadatos:
            if datos.id in self._metadatos:
                raise ValueError("ID de metadatos duplicado en fixture")
            self._metadatos[datos.id] = datos
        for sala in salas:
            if sala.id in self._salas:
                raise ValueError("ID de sala duplicado en fixture")
            self._salas[sala.id] = sala
        # Envoltorio del catálogo existente del motor; no índice de rutas/mapa.
        self.catalogo = {
            "guardian": Enemy("guardian", "Guardián", 20, 4, 1, 10, "guardián", []),
            "antorcha": Torch("antorcha", "Antorcha", 1, 1, 1200),
            "pergamino": RewindScroll("pergamino", "Pergamino", 1, 1),
            "cura": Potion("cura", "Poción", 1, 1, cura=20),
            "llave": Key("llave", "Llave", 1, 1, abre=LEJANA),
            "pinchos": Trap("pinchos", "Pinchos", 3),
            "veneno": Trap("veneno", "Veneno", 1, veneno=2),
            "fuego": Trap("fuego", "Fuego", 1, quemadura=2),
        }
        self.consultas_metadatos: list[int] = []
        self.consultas_contenido: list[int] = []
        self.consultas_fichas: list[str] = []
        self.activaciones: list[int] = []
        self._restriccion_metadatos = 0

    @contextmanager
    def solo_metadatos(self):
        self._restriccion_metadatos += 1
        try:
            yield self
        finally:
            self._restriccion_metadatos -= 1

    def _exigir_contenido_permitido(self):
        if self._restriccion_metadatos:
            raise AssertionError("revelación/ruta consultó contenido o activó una sala")

    def datos_sala(self, sala_id: int) -> DatosSala:
        self.consultas_metadatos.append(sala_id)
        try:
            return self._metadatos[sala_id]
        except KeyError:
            raise NotFoundError(f"Sala {sala_id} inexistente") from None

    def sala_lista(self, sala_id: int) -> SalaViva:
        self.consultas_contenido.append(sala_id)
        self._exigir_contenido_permitido()
        try:
            return self._salas[sala_id]
        except KeyError:
            raise NotFoundError(f"Sala {sala_id} inexistente") from None

    def ficha(self, ficha_id: str):
        self.consultas_fichas.append(ficha_id)
        self._exigir_contenido_permitido()
        return self.catalogo[ficha_id]

    def activar(self, sala_id: int):
        """Sonda para consumidores de prueba; no reemplaza activación del motor."""
        self._exigir_contenido_permitido()
        self.activaciones.append(sala_id)
        for enemigo in self._salas[sala_id].enemigos:
            if enemigo.vivo:
                enemigo.activa = True


def crear_proveedor_niebla() -> ProveedorNiebla:
    metadatos = (
        DatosSala(INICIO, "Entrada", (
            DatosSalida("E", VECINA, 9, (INICIO, "E")),
            DatosSalida("N", VECINA, 9, (INICIO, "N")),  # arco paralelo distinto
        )),
        DatosSala(VECINA, "Capilla", (
            DatosSalida("O", INICIO, 9, (INICIO, "E")),  # recíproca declarada
            DatosSalida("N", LEJANA, 1, (VECINA, "N")),
            DatosSalida("E", AISLADA, 4, (VECINA, "E")),  # sin recíproca
        )),
        DatosSala(LEJANA, "Cripta", (
            DatosSalida("S", VECINA, 1, (VECINA, "N")),
        )),
        DatosSala(AISLADA, "Sin salida", ()),
    )
    salas = []
    for datos in metadatos:
        sala = SalaViva(datos.id, datos.nombre)
        for salida in datos.salidas:
            sala.salidas[salida.direccion] = SalidaPonderadaFalsa(
                direccion=salida.direccion, destino=salida.destino,
                cerrada=salida.puerta_id == (VECINA, "N"),
                llave="llave" if salida.puerta_id == (VECINA, "N") else None,
                costo=salida.costo,
            )
        if datos.id == INICIO:
            sala.objetos_suelo = ["antorcha", "pergamino", "cura", "llave"]
        elif datos.id == VECINA:
            sala.enemigos = [
                EnemigoInstancia("dormido", "guardian", 20, VECINA),
                EnemigoInstancia("muerto", "guardian", 0, VECINA),
            ]
            sala.trampas = [TrampaInstancia("pinchos-1", "pinchos", VECINA)]
        elif datos.id == LEJANA:
            sala.enemigos = [EnemigoInstancia("activo", "guardian", 20, LEJANA, activa=True)]
            sala.trampas = [
                TrampaInstancia("veneno-1", "veneno", LEJANA),
                TrampaInstancia("fuego-1", "fuego", LEJANA),
            ]
        salas.append(sala)
    return ProveedorNiebla(metadatos, tuple(salas))


def crear_jugador_niebla() -> JugadorVivo:
    return JugadorVivo(100, 100, 10, 5, 10,
                       inventario=["antorcha", "pergamino", "cura", "llave"],
                       efectos={"veneno": 400, "quemadura": 200})


@pytest.fixture
def proveedor_niebla():
    return crear_proveedor_niebla()


@pytest.fixture
def sesion_niebla():
    from src.controller2.fachada import Fachada
    from src.controller2.modelo import EstadoPartida
    from src.orchestrator.sesion import Sesion
    proveedor = crear_proveedor_niebla()
    jugador = crear_jugador_niebla()
    jugador.efectos.clear()
    estado = EstadoPartida("niebla", "v1", "cat1", INICIO, -1, "salida", 20, jugador,
                          salas={s.id: s for s in proveedor._salas.valores()}, salas_visitadas=[INICIO])
    sesion = Sesion(backend=object())
    sesion.estado, sesion.proveedor = estado, proveedor
    sesion.fachada = Fachada(estado, proveedor, proveedor.catalogo, bitacora=sesion._mem,
                             oleada_cada=100000)
    return sesion
