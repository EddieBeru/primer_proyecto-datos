import time

from models.errors import PresupuestoAgotadoError

class BudgetAdapter:
    def __init__(self, presupuesto = 14):
        self.presupuesto = presupuesto

    def ejecutar(self, peticion, max_intentos, espera):
        ultimo = None
        for intento in range(max_intentos):
            self.gastar()
            try:
                return peticion()
            except (PresupuestoAgotadoError, Exception) as e:
                ultimo = e
                if intento < max_intentos - 1:
                    time.sleep(espera)
        raise ultimo

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
