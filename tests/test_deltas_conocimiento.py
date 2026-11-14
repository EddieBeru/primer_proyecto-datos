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


def test_receptor_inicio_evento_y_reaplicacion_bidireccional():
    from fixtures_niebla import crear_proveedor_niebla, crear_jugador_niebla
    from src.controller2.fachada import Fachada
    from src.controller2.modelo import EstadoPartida
    from src.controller2.conocimiento import MapaConocido
    class Colector:
        def __init__(self):
            self.lotes = []
        def registrar_cambios(self, contexto, lote):
            self.lotes.append((contexto, lote))
        def truncar_ultimo_intervalo(self):
            pass
    proveedor = crear_proveedor_niebla()
    estado = EstadoPartida('niebla', 'v1', 'cat1', INICIO, -1, 'salida', 20,
        crear_jugador_niebla(), salas={s.id:s for s in proveedor._salas.valores()})
    estado.jugador.efectos.clear()
    colector = Colector()
    f = Fachada(estado, proveedor, proveedor.catalogo, receptor_cambios=colector)
    assert colector.lotes[0][0]['clase'] == 'inicio'
    # Evento local ordinario: cierre en la sala actual.
    f.agenda.programar(1, 'cierre_puerta', {'sala': INICIO, 'direccion':'E'})
    f.avanzar()
    assert any(contexto['clase'] == 'evento' for contexto, _ in colector.lotes)
    reconstruido = MapaConocido()
    for contexto, lote in colector.lotes:
        for cambio in lote:
            reconstruido.aplicar(cambio)
    assert reconstruido == estado.conocimiento
    for contexto, lote in reversed(colector.lotes):
        for cambio in reversed(lote):
            reconstruido.aplicar(cambio, adelante=False)
    assert reconstruido.a_dict() == {'salas': [], 'puertas': []}


def test_entrada_con_antorcha_revela_sin_activar_y_deshace(sesion_niebla):
    """FR-NIE-06/07/08: Apéndice B, entrada con antorcha y su retroceso."""
    ses = sesion_niebla
    assert ses.paso('usar antorcha')[0]
    antes = ses.estado.conocimiento.a_dict()
    # Entrar a5 revela LEJANA/999, sin disparar sus enemigos/trampas.
    ses.estado.salas[VECINA].enemigos.clear()
    ses.estado.salas[VECINA].trampas.clear()
    ses.proveedor.consultas_contenido.clear()
    for enemigo in ses.estado.salas[LEJANA].enemigos:
        enemigo.activa = False
    assert ses.paso('e')[0]
    assert ses.estado.conocimiento.sala(LEJANA).estado == 'explorada'
    assert all(t.armada for t in ses.estado.salas[LEJANA].trampas)
    assert all(not e.activa for e in ses.estado.salas[LEJANA].enemigos)
    assert ses.proveedor.consultas_contenido == []
    assert ses.paso('deshacer')[0]
    assert ses.estado.sala_actual == INICIO
    assert ses.estado.conocimiento.a_dict() == antes


def test_receptor_historia_004_concuerda_con_deltas_002(sesion_niebla):
    """FR-NIE-08 (T052): con004 real, los deltas de002 y la historia reconstruyen lo mismo."""
    from src.controller2.conocimiento import MapaConocido
    from src.controller2.linea_tiempo import LineaTiempo, conocimiento_serializado
    ses = sesion_niebla

    class Colector:
        def __init__(self):
            self.lotes = []
        def registrar_cambios(self, contexto, lote):
            self.lotes.append((contexto, lote))
        def truncar_ultimo_intervalo(self):
            pass

    colector = Colector()
    ses.fachada.receptor_cambios = colector
    raiz = conocimiento_serializado(ses.estado)  # conocimiento del 'inicio' de002
    ses.linea = LineaTiempo(ses.estado, 2)
    ses.fachada.receptor_historia = ses.linea
    assert ses.paso('usar antorcha')[0]
    torch = conocimiento_serializado(ses.estado)
    # Entrar sin daño para aislar solo el conocimiento.
    ses.estado.salas[VECINA].enemigos.clear()
    ses.estado.salas[VECINA].trampas.clear()
    for enemigo in ses.estado.salas[LEJANA].enemigos:
        enemigo.activa = False
    assert ses.paso('e')[0]
    entrada = conocimiento_serializado(ses.estado)
    # Los deltas de002 reaplican la misma evolución del conocimiento.
    mapa = MapaConocido.desde_dict(raiz)
    for _, lote in colector.lotes:
        for cambio in lote:
            mapa.aplicar(cambio)
    assert mapa == ses.estado.conocimiento
    # La historia de004 reconstruye el conocimiento en cada frontera de acción.
    linea = ses.linea
    assert linea.reconstruir(linea.acciones[0][0])['conocimiento'] == raiz
    assert linea.reconstruir(linea.acciones[1][0])['conocimiento'] == torch
    assert linea.reconstruir(len(linea.registros))['conocimiento'] == entrada
    # Antes de la antorcha la lejana era ausente/avistada; la entrada la explora.
    estados = lambda r: {f[0]: f[2] for f in r.mapa}
    assert LEJANA not in estados(ses.historia_accion(1))
    assert estados(ses.historia_accion(2))[LEJANA] == 'avistada'
    assert estados(ses.historia(ses.estado.reloj))[LEJANA] == 'explorada'
    # El retroceso restaura la rama histórica hasta la antorcha (P1 y 004 de acuerdo).
    assert ses.paso('deshacer')[0]
    assert conocimiento_serializado(ses.estado) == torch
    assert linea.reconstruir(len(linea.registros))['conocimiento'] == torch
