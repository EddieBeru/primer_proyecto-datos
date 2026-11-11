"""Bucle real de consola con entrada y reloj virtuales, sin terminal."""
import pytest
from fixtures_niebla import sesion_niebla, INICIO, VECINA, LEJANA
from src.orchestrator.consola import bucle


@pytest.mark.parametrize('consulta', ['mapa', 'foto', 'inventario', 'ayuda', 'cargar inexistente.bin'])
def test_consultas_y_carga_fallida_preservan_continuacion(sesion_niebla, consulta, monkeypatch):
    ses = sesion_niebla
    ses.estado.conocimiento.revelar(INICIO, ses.proveedor.datos_sala, True)
    ses.estado.salas[VECINA].enemigos.clear()
    ses.estado.salas[VECINA].trampas.clear()
    monkeypatch.setattr(ses, "finalizar", lambda: {"terminada": False})
    ahora = [0.0]
    comandos = iter(['ir a 5', 'salir'])
    entradas = iter([consulta, None, 'cancelar'])
    vistas = []
    def leer(espera):
        texto = next(entradas)
        if texto is None:
            assert ses.fachada.viaje.activo
            assert ses.estado.sala_actual == INICIO
            ahora[0] += espera
        return texto
    assert bucle(ses, entrada=lambda _: next(comandos), salida=vistas.append,
                 leer_viaje=leer, reloj=lambda: ahora[0]) == 0
    assert ses.estado.sala_actual == VECINA
    assert ses.estado.acciones_jugador == 1
    if consulta.startswith('cargar'):
        assert any('no se pudo cargar' in v for v in vistas)


@pytest.mark.parametrize('excepcion', [EOFError, KeyboardInterrupt])
def test_interrupcion_cancela_sin_avanzar(sesion_niebla, excepcion):
    ses = sesion_niebla
    ses.estado.conocimiento.revelar(INICIO, ses.proveedor.datos_sala, True)
    ses.paso('ir a 5')
    def leer(_):
        raise excepcion
    assert bucle(ses, salida=lambda _: None, leer_viaje=leer, reloj=lambda: 0) == 130
    assert not ses.fachada.viaje.activo
    assert ses.estado.sala_actual == INICIO


@pytest.mark.parametrize('comando', ['guardar', 'cargar'])
def test_guardar_y_cargar_validos_cancelan_en_bucle(tmp_path, comando):
    from test_sesion import nueva_sesion, CRIPTA_ID
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    ses.estado.sala_en_curso().enemigos.clear()
    ses.estado.conocimiento.revelar(1, ses.proveedor.datos_sala, True)
    ruta = str(tmp_path/'viaje.bin')
    ses.guardar(ruta)
    ses.paso('ir a 2')
    def entrada(_):
        raise EOFError
    assert bucle(ses, entrada=entrada, salida=lambda _:None,
        leer_viaje=lambda _: f'{comando} {ruta}', reloj=lambda:0) == 130
    assert ses.estado.sala_actual == 1
    assert not ses.fachada.viaje.activo
