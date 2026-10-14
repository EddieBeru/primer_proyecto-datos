
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from src.models.dungeons import DungeonGeneral, PlayerInitial
from src.models.roomContents import EnemyPlacement, RoomContentEntry, TrapPlacement
from src.models.rooms import Exit, Room

Direccion = Literal["N", "S", "E", "O"]
EstadoJuego = Literal["jugando", "victoria", "derrota"]

# Valores por defecto para campos que el API puede traer vacios.
# Acordados en Fase 0; marcados como pendientes de confirmar con el profe.
# (docs: "separacion vista controlador.md" 2.7, "vista y flujos api.md" Parte 4).
# TODO(profe pregunta 3): confirmar que "vacio" significa estos defaults y no "no aplica".
# TODO(profe pregunta 1): confirmar si version/reintentos descuentan; afecta presupuesto_restante.
DEFAULTS: dict[str, Any] = {
    # Exit.cerrada ausente -> puerta abierta.
    "cerrada": False,
    # Exit.llave ausente -> no pide llave.
    "llave": None,
    # Exit.cierre_automatico ausente -> no se cierra sola.
    "cierre_automatico": None,
    # EnemyPlacement.vida ausente -> vida_max del tipo (se resuelve al hidratar).
    "vida_instancia": None,
    # Trampa nueva -> armada. Trap.rearme ausente -> un solo uso, no se rearma.
    "trampa_armada_inicial": True,
    "rearme": None,
    # Potion.cura / modificador_velocidad / duracion ausentes -> sin efecto.
    "cura": 0,
    "modificador_velocidad": 0,
    "duracion": 0,
    # Key.abre ausente o vacio -> PENDIENTE profe (preguntas 2 y 8).
    # Supuesto temporal: la llave vale si su id == salida.llave.
    # TODO(profe pregunta 2): confirmar si manda salida.llave o Key.abre cuando hay conflicto.
    "abre": None,
    # Rastro fresco para rastreador (C2-8): 0 = sin rastro.
    # TODO(profe pregunta 7 + C2-8): confirmar regla de frescura/duracion del rastro.
    "rastro": 0,
}

_DIRECCIONES_VALIDAS = ("N", "S", "E", "O")


# ---------------------------------------------------------------------------
# Jugador
# ---------------------------------------------------------------------------

@dataclass
class JugadorVivo:
    """Estado cambiante del jugador.

    El inventario es ``list[str]`` con ids de catalogo EN ORDEN; la posicion 0
    es el frente (equipo resaltado, segun guia). C2-5 reemplazara la lista por
    su lista doblemente enlazada propia sin cambiar este contrato: el orden
    visible y las operaciones (recoger/soltar/equipar/recorrer) se mantienen.

    ``efectos`` es ``{nombre: turnos_restantes}`` para no congelar el contrato
    antes de C2-7. Ej: {"veneno": 3, "veloz": 5, "antorcha": 10}.
    """

    # TODO(C2-5): sincronizar este orden con el Inventario enlazado (a_lista/desde_jugador).
    # TODO(C1-8): esta lista en orden es lo que se guarda a bytes (K2).
    # TODO(C2-7): veneno/pocion/antorcha/antidoto consumen `efectos` + agenda.
    vida_max: int
    vida_actual: int
    ataque: int
    defensa: int
    velocidad: int
    inventario: list[str] = field(default_factory=list)
    arma_equipada: str | None = None
    armadura_equipada: str | None = None
    efectos: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.vida_max <= 0:
            raise ValueError("vida_max debe ser > 0")
        if self.velocidad <= 0:
            raise ValueError("velocidad debe ser > 0")
        if not 0 <= self.vida_actual <= self.vida_max:
            raise ValueError("vida_actual debe estar en [0, vida_max]")

    @classmethod
    def desde_inicial(cls, base: PlayerInitial) -> "JugadorVivo":
        """Crea al jugador al inicio (Flujo B): vida llena, mochila vacia."""
        return cls(
            vida_max=base.vida_max,
            vida_actual=base.vida_max,
            ataque=base.ataque,
            defensa=base.defensa,
            velocidad=base.velocidad,
        )

    # -- consultas que usan Vista y C2-6/C2-10 sin conocer el catalogo --
    @property
    def vivo(self) -> bool:
        return self.vida_actual > 0

    def tiene_llave(self, llave_id: str | None) -> bool:
        if llave_id is None:
            return True
        return llave_id in self.inventario

    def ataque_total(self, arma_bonus: int = 0) -> int:
        return self.ataque + arma_bonus

    def defensa_total(self, armadura_bonus: int = 0) -> int:
        return self.defensa + armadura_bonus

    def recibir_dano(self, cantidad: int) -> None:
        self.vida_actual = max(0, self.vida_actual - max(0, int(cantidad)))

    def curar(self, cantidad: int) -> None:
        self.vida_actual = min(self.vida_max, self.vida_actual + max(0, int(cantidad)))


# ---------------------------------------------------------------------------
# Puerta / salida viva
# ---------------------------------------------------------------------------

@dataclass
class SalidaViva:

    direccion: Direccion
    destino: int
    cerrada: bool = DEFAULTS["cerrada"]
    llave: str | None = DEFAULTS["llave"]
    cierre_automatico: int | None = DEFAULTS["cierre_automatico"]

    def __post_init__(self) -> None:
        if self.direccion not in _DIRECCIONES_VALIDAS:
            raise ValueError(f"direccion invalida: {self.direccion!r}")
        if self.cierre_automatico is not None and self.cierre_automatico <= 0:
            raise ValueError("cierre_automatico debe ser > 0 o None")

    @classmethod
    def desde_api(cls, direccion: Direccion, salida: Exit) -> "SalidaViva":
        return cls(
            direccion=direccion,
            destino=salida.sala,
            cerrada=salida.cerrada if salida.cerrada is not None else DEFAULTS["cerrada"],
            llave=salida.llave if salida.llave is not None else DEFAULTS["llave"],
            cierre_automatico=(
                salida.cierre_automatico
                if salida.cierre_automatico is not None
                else DEFAULTS["cierre_automatico"]
            ),
        )

    def puede_pasar(self, jugador: JugadorVivo) -> tuple[bool, str]:
        """Regla Flujo E. Devuelve (ok, mensaje). No muta nada."""
        if not self.cerrada:
            return True, ""
        if self.llave is None:
            return False, "Puerta trabada."
        if jugador.tiene_llave(self.llave):
            return True, ""
        return False, f"Necesitas la llave {self.llave}."


# ---------------------------------------------------------------------------
# Instancias (enemigos y trampas concretos)
# ---------------------------------------------------------------------------

@dataclass
class EnemigoInstancia:
    """UN enemigo concreto: instancia + tipo + vida propia."""

    instancia: str
    tipo_id: str
    vida_actual: int
    sala_actual: int

    @classmethod
    def desde_colocacion(
        cls, col: EnemyPlacement, sala: int, vida_max_tipo: int
    ) -> "EnemigoInstancia":
        """``vida`` vacia -> vida_max del tipo (DEFAULTS pendiente profe)."""
        # TODO(profe pregunta 3): confirmar que vida vacia = vida_max del tipo.
        # TODO(C1-7): `vida_max_tipo` viene de la ficha del catalogo (cache LRU C1-6).
        vida = col.vida if col.vida is not None else vida_max_tipo
        return cls(instancia=col.instancia, tipo_id=col.tipo, vida_actual=vida, sala_actual=sala)

    @property
    def vivo(self) -> bool:
        return self.vida_actual > 0

    def recibir_dano(self, cantidad: int) -> None:
        self.vida_actual = max(0, self.vida_actual - max(0, int(cantidad)))


@dataclass
class TrampaInstancia:
    """UNA trampa concreta: instancia + tipo + armada o no."""

    instancia: str
    tipo_id: str
    sala: int
    armada: bool = True

    @classmethod
    def desde_colocacion(cls, col: TrapPlacement, sala: int) -> "TrampaInstancia":
        return cls(
            instancia=col.instancia,
            tipo_id=col.tipo,
            sala=sala,
            armada=DEFAULTS["trampa_armada_inicial"],
        )


# ---------------------------------------------------------------------------
# Sala viva
# ---------------------------------------------------------------------------

@dataclass
class SalaViva:
    """Sala lista para jugar y dibujar (Flujo C hecho dato).

    * ``salidas``: estado vivo de puertas (lo que la Vista dibuja).
    * ``enemigos`` / ``trampas``: instancias con estado propio.
    * ``objetos_suelo``: ids de catalogo simples, sin instancia.
    * ``rastro``: intensidad del paso del jugador (C2-8 rastreador).
    """

    id: int
    nombre: str
    salidas: dict[str, SalidaViva] = field(default_factory=dict)
    enemigos: list[EnemigoInstancia] = field(default_factory=list)
    objetos_suelo: list[str] = field(default_factory=list)
    trampas: list[TrampaInstancia] = field(default_factory=list)
    visitada: bool = False
    rastro: int = DEFAULTS["rastro"]
    # TODO(C1-7): esta es la "sala lista" que arma C1 (Flujo C: contenido + catalogo).
    # TODO(C2-8): `rastro` lo consume el rastreador; falta decaimiento con agenda.

    @classmethod
    def desde_esqueleto(cls, sala: Room) -> "SalaViva":
        """Paso 1: mapa sin contenido (endpoints 4 + 2)."""
        salidas = {
            d: SalidaViva.desde_api(d, s)  # type: ignore[arg-type]
            for d, s in (sala.salidas or {}).items()
            if d in _DIRECCIONES_VALIDAS
        }
        return cls(id=sala.id, nombre=sala.nombre, salidas=salidas)

    def hidratar_contenido(
        self, contenido: RoomContentEntry, vidas_max: dict[str, int] | None = None
    ) -> None:
        """Paso 2 (C1-7): viste la sala con enemigos/objetos/trampas.

        ``vidas_max``: {tipo_id: vida_max} del catalogo para resolver
        ``vida`` vacia. Si falta un tipo, se usa 1 para no frenar a C1;
        el combate real (C2-6) exigira la ficha.
        """
        vidas_max = vidas_max or {}
        self.enemigos = [
            EnemigoInstancia.desde_colocacion(e, self.id, vidas_max.get(e.tipo, 1))
            for e in (contenido.enemigos or [])
        ]
        self.objetos_suelo = list(contenido.objetos or [])
        self.trampas = [TrampaInstancia.desde_colocacion(t, self.id) for t in (contenido.trampas or [])]

    def enemigos_vivos(self) -> list[EnemigoInstancia]:
        return [e for e in self.enemigos if e.vivo]


# ---------------------------------------------------------------------------
# Estado de partida (dueno: C2. Formato bytes: C1. Contrato K2.)
# ---------------------------------------------------------------------------

@dataclass
class EstadoPartida:
    """Todo lo que forma una partida (K2, Flujo G). Campos fijos.

    Si C2 necesita un dato nuevo, lo agrega aqui Y avisa a C1 (regla 6.3),
    porque C1-8 lo escribe a disco con struct.
    """

    cripta_id: str
    version_cripta: str
    version_catalogo: str
    sala_actual: int
    sala_salida: int
    llave_salida: str
    inventario_max: int
    jugador: JugadorVivo
    salas: dict[int, SalaViva] = field(default_factory=dict)
    salas_visitadas: list[int] = field(default_factory=list)
    reloj: int = 0
    presupuesto_restante: int = 0
    # Placeholders con forma minima para no bloquear a C1-8:
    # agenda C2-2: [{t, seq, tipo, datos}]; pila C2-9: [{inversa, datos}].
    # TODO(C2-2 hecho): Agenda.a_lista/desde_lista ya produce esta forma; falta cablear reloj<->EstadoPartida.
    # TODO(C2-9): definir forma final de cada entrada de pila_deshacer (accion inversa, no copia total).
    # TODO(C1-8): C1 serializa estos dos campos a bytes con struct; avisar si cambia su forma (regla 6.3).
    agenda: list[dict[str, Any]] = field(default_factory=list)
    pila_deshacer: list[dict[str, Any]] = field(default_factory=list)
    estado: EstadoJuego = "jugando"
    # TODO(C2-10): `estado` y puntaje los decide fin-de-juego; pendiente formula de puntaje (profe pregunta 9).
    # TODO(C2-11/C1-9): cada cambio aqui debe anotarse a bitacora (K3) para --replay.

    @classmethod
    def nueva_partida(cls, ficha: DungeonGeneral, version_catalogo: str) -> "EstadoPartida":
        """Estado inicial (Flujo B): jugador lleno, reloj 0, sin salas aun."""
        return cls(
            cripta_id=ficha.id,
            version_cripta=ficha.version,
            version_catalogo=version_catalogo,
            sala_actual=ficha.sala_inicial,
            sala_salida=ficha.sala_salida,
            llave_salida=ficha.llave_salida,
            inventario_max=ficha.inventario_max,
            jugador=JugadorVivo.desde_inicial(ficha.jugador),
            salas={},
            salas_visitadas=[ficha.sala_inicial],
            reloj=0,
            presupuesto_restante=ficha.presupuesto_solicitudes,
            agenda=[],
            pila_deshacer=[],
            estado="jugando",
        )

    def registrar_sala(self, sala: SalaViva) -> None:
        self.salas[sala.id] = sala
        if sala.id not in self.salas_visitadas:
            self.salas_visitadas.append(sala.id)

    def sala_en_curso(self) -> SalaViva:
        return self.salas[self.sala_actual]

    # -- serializacion para C1-8 (C2 entrega dict, C1 lo pasa a bytes) --
    def a_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def desde_dict(cls, data: dict[str, Any]) -> "EstadoPartida":
        d = dict(data)
        d["jugador"] = JugadorVivo(**d["jugador"])
        salas = {}
        for sid, s in (d.get("salas") or {}).items():
            s = dict(s)
            s["salidas"] = {k: SalidaViva(**v) for k, v in (s.get("salidas") or {}).items()}
            s["enemigos"] = [EnemigoInstancia(**e) for e in (s.get("enemigos") or [])]
            s["trampas"] = [TrampaInstancia(**t) for t in (s.get("trampas") or [])]
            salas[int(sid)] = SalaViva(**s)
        d["salas"] = salas
        return cls(**d)
