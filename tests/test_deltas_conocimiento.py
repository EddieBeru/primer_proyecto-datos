from fixtures_niebla import INICIO, VECINA, LEJANA, sesion_niebla


def test_entrada_y_antorcha_reversibles(sesion_niebla):
    ses = sesion_niebla
    antes = ses.estado.conocimiento.a_dict()
    assert ses.paso("usar antorcha")[0]
    assert ses.estado.conocimiento.sala(VECINA).estado == "explorada"
    assert ses.paso("deshacer")[0]
    assert ses.estado.conocimiento.a_dict() == antes
    assert "antorcha" not in ses.estado.jugador.efectos
    assert "antorcha" in ses.estado.jugador.inventario


def test_reencendido_restaura_efecto_y_evento_anterior(sesion_niebla):
    ses = sesion_niebla
    ses.paso("usar antorcha")
    anteriores = [e for e in ses.fachada.agenda if e.tipo == "fin_efecto" and e.datos.get("efecto") == "antorcha"]
    ses.estado.jugador.inventario.append("antorcha")
    ses.paso("usar antorcha")
    assert ses.paso("deshacer")[0]
    actuales = [e for e in ses.fachada.agenda if e.tipo == "fin_efecto" and e.datos.get("efecto") == "antorcha"]
    assert [(e.t,e.seq) for e in actuales] == [(e.t,e.seq) for e in anteriores]
    assert ses.estado.jugador.efectos["antorcha"] == 1200


def test_receptor_obtiene_deltas_antes_de_descartar_y_truncamiento(sesion_niebla):
    ses = sesion_niebla
    class Colector:
        def __init__(self):
            self.lotes, self.truncamientos = [], 0
        def registrar_cambios(self, contexto, lote):
            self.lotes.append((contexto, lote))
        def truncar_ultimo_intervalo(self):
            self.truncamientos += 1
    colector = Colector()
    ses.fachada.receptor_cambios = colector
    for n in range(8):
        # Cambiar físicamente una puerta produce un delta local por evento causal.
        ses.estado.salas[INICIO].salidas["E"].cerrada = bool(n % 2)
        ses.paso("esperar")
    assert len(colector.lotes) >= 7
    assert all(c["clase"] == "accion" for c,l in colector.lotes)
    assert [c["orden"] for c,l in colector.lotes] == list(range(1, len(colector.lotes)+1))
    assert ses.fachada.pila.intervalos == 5
    ses.paso("deshacer")
    assert colector.truncamientos == 1
