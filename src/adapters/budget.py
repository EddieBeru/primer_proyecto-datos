from src.models.errors import PresupuestoAgotadoError


class BudgetAdapter:
    """Contador C1-3 (§5.1 doc oficial).

    Toda solicitud HTTP cuenta: lista, ficha, páginas, contenido, catálogo,
    versiones y reintentos 429. Local/offline no cuenta (no pasa por aquí).
    """

    def __init__(self, presupuesto=14):
        if presupuesto < 0:
            raise ValueError(f"presupuesto inicial inválido: {presupuesto}")
        self.presupuesto = presupuesto
        self.inicial = presupuesto
        self.realizadas = 0
        self.hits = 0
        self.misses = 0

    def get_presupuesto(self):
        return self.presupuesto

    def puede_mas(self):
        return self.presupuesto > 0

    def gastar(self):
        if not self.puede_mas():
            raise PresupuestoAgotadoError("No hay suficiente presupuesto")
        self.presupuesto -= 1
        self.realizadas += 1

    def hit(self):
        self.hits += 1

    def miss(self):
        self.misses += 1

    def reporte(self) -> dict:
        return {"realizadas": self.realizadas, "presupuesto": self.inicial,
                "restantes": self.presupuesto, "hits": self.hits, "misses": self.misses}

    def reiniciar(self, presupuesto=14):
        if presupuesto < 0:
            raise ValueError(f"presupuesto inicial inválido: {presupuesto}")
        self.presupuesto = presupuesto
        self.inicial = presupuesto
        self.realizadas = 0
        self.hits = 0
        self.misses = 0
