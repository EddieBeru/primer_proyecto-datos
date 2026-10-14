from src.models.errors import PresupuestoAgotadoError

class BudgetAdapter:
    def __init__(self, presupuesto = 14):
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
        self.presupuesto = presupuesto
