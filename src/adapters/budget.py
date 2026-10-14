from src.models.errors import PresupuestoAgotadoError

class BudgetAdapter:
    """Contador C1-3. Cada intento HTTP cuesta 1 vía gastar().

    Se crea con iniciar_cripta() (session.py), no a mano.
    """

    def __init__(self, presupuesto = 14):
        if presupuesto < 0:
            raise ValueError(f"presupuesto inicial inválido: {presupuesto}")
        self.presupuesto = presupuesto

    def get_presupuesto(self):
        return self.presupuesto

    def puede_mas(self):
        return self.presupuesto > 0

    def gastar(self):
        if not self.puede_mas():
            raise PresupuestoAgotadoError("No hay suficiente presupuesto")
        self.presupuesto -= 1

    def reiniciar(self, presupuesto = 14):
        if presupuesto < 0:
            raise ValueError(f"presupuesto inicial inválido: {presupuesto}")
        self.presupuesto = presupuesto
