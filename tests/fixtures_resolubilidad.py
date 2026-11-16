"""Fixtures puras para verificación: conservan el orden declarado de entrada.

No hacen llamadas HTTP ni contienen lógica de resolución. Cada constructor deja
explícito qué salas, salidas y ubicaciones forman parte del caso.
"""

from src.models.rooms import Exit, Room


def esqueleto(salas):
    """Construye el índice existente conservando el orden de la secuencia."""
    return {sala.id: sala for sala in salas}


def sala(id_, nombre, **salidas):
    """Una sala cuyas salidas se entregan en orden de argumentos."""
    return Room(id=id_, nombre=nombre, salidas={
        direccion: valor if isinstance(valor, Exit) else Exit(**valor)
        for direccion, valor in salidas.items()
    })


def ubicacion(llave, sala_id, enemigo=None):
    """Entrada de transporte; `sala_id` es siempre la sala inicial."""
    return {"id": llave, "sala": sala_id, "enemigo": enemigo}


def escenario_resoluble():
    """Entrada→tesoro→salida; llave final local en sala de tesoro."""
    return (
        esqueleto((sala(1, "Entrada", E={"sala": 2}),
                   sala(2, "Tesoro", E={"sala": 3, "llave": "final",
                                           "cerrada": True}),
                   sala(3, "Salida"))),
        (ubicacion("paso", 1), ubicacion("final", 2)),
        {"sala_inicial": 1, "sala_salida": 3, "llave_salida": "final"},
    )


def escenario_ciclo():
    """Llave final en sala tras la puerta final: no hay progreso inicial."""
    return (
        esqueleto((sala(1, "Entrada", E={"sala": 2, "llave": "final",
                                             "cerrada": True}),
                   sala(2, "Salida"))),
        (ubicacion("final", 2),),
        {"sala_inicial": 1, "sala_salida": 2, "llave_salida": "final"},
    )


def escenario_incompleto():
    """Respuesta parcial que no autoriza un veredicto."""
    return ({1: sala(1, "Entrada")}, (),
            {"sala_inicial": 1, "sala_salida": 1, "llave_salida": "final",
             "completa": False})


def escenario_errante():
    """Enemigo errante: la llave se declara en su posición inicial."""
    return ({1: sala(1, "Inicio", E={"sala": 2, "llave": "caida",
                                        "cerrada": True}),
             2: sala(2, "Salida")}, (ubicacion("caida", 1, "enemigo-1"),),
            {"sala_inicial": 1, "sala_salida": 2, "llave_salida": "caida"})


def escenario_alternativas():
    """Una llave con dos ubicaciones; primera ubicación conserva precedencia."""
    return ({1: sala(1, "Inicio")},
            (ubicacion("opcional", 3), ubicacion("opcional", 2)),
            {"sala_inicial": 1, "sala_salida": 1, "llave_salida": "opcional"})
