"""Aceptación de costos/cazador con conocimiento, historia, carga y replay reales."""
from test_sesion import FakeBackend, nueva_sesion, CRIPTA_ID
from src.controller2.linea_tiempo import estado_serializado


def backend_integrado():
    backend = FakeBackend()
    for contenido in backend.fake._contenido.values():
        contenido.enemigos.clear()
        contenido.trampas.clear()
    from src.models.roomContents import EnemyPlacement
    backend.fake._contenido[1].enemigos = [EnemyPlacement('caz-inicial', 'esqueleto-guardian-01')]
    backend.fake._contenido[1].objetos.append('pergamino-01')
    ficha = backend.fake._fichas['esqueleto-guardian-01']
    ficha.comportamiento, ficha.rango, ficha.velocidad = 'cazador', 1000, 10
    backend.fake._general.jugador.vida_max = 1000
    backend.fake._salas[1].salidas['E'].costo = 250
    backend.fake._salas[2].salidas['O'].costo = 250
    return backend


def test_costos_cazador_historia_carga_replay_y_deshacer(tmp_path):
    ses = nueva_sesion(tmp_path, backend=backend_integrado(), checkpoint_cada=2)
    ses.iniciar(CRIPTA_ID, semilla=29)
    anteriores = []
    for comando in ('recoger pergamino-01', 'e', 'esperar'):
        anteriores.append(estado_serializado(ses.estado))
        assert ses.paso(comando)[0]
    assert ses.estado.sala_actual == 2
    assert any(e.instancia == 'caz-inicial' for e in ses.estado.salas[2].enemigos)
    assert ses.estado.reloj == 3750
    for i, esperado in enumerate(anteriores):
        assert ses.linea.reconstruir(ses.linea.acciones[i][0]) == esperado
    consultas = [ses.historia_accion(i) for i in (1,2,3)]
    antes_carga = estado_serializado(ses.estado)
    ruta = str(tmp_path/'integrada.bin')
    ses.guardar(ruta)
    otra = nueva_sesion(tmp_path, backend=backend_integrado(), log_ruta=None, checkpoint_cada=2)
    otra.cargar_en_frio(ruta)
    assert [otra.historia_accion(i) for i in (1,2,3)] == consultas
    for campo in ('salas','agenda','reloj','azar_estado','pila_deshacer'):
        assert estado_serializado(otra.estado)[campo] == antes_carga[campo]
    replay = nueva_sesion(tmp_path, backend=backend_integrado(), log_ruta=None, checkpoint_cada=2)
    replay.reproducir(str(tmp_path/'p.log'))
    assert estado_serializado(replay.estado) == antes_carga
    assert [replay.historia_accion(i) for i in (1,2,3)] == consultas
    # Retroceso después de carga elimina el último intervalo y su RNG/turnos.
    assert otra.paso('deshacer')[0]
    esperado = anteriores[-1]
    for campo in ('salas','reloj','azar_estado','azar_llamadas'):
        assert estado_serializado(otra.estado)[campo] == esperado[campo]
    assert otra.linea.acciones[-1][2] == 'deshacer'
    assert otra.paso('esperar')[0]


def test_guardado_v4_anterior_sin_rng_en_inversa_migra_al_deshacer(tmp_path):
    from src.controller1 import savegame
    ses = nueva_sesion(tmp_path, backend=backend_integrado())
    ses.iniciar(CRIPTA_ID, semilla=29)
    for comando in ('recoger pergamino-01', 'e'):
        assert ses.paso(comando)[0]
    antes = estado_serializado(ses.estado)
    assert ses.paso('esperar')[0]
    datos = ses.fachada.guardar()
    datos['historia'] = ses.linea.a_dict()
    # Proyectar exactamente el esquema previo de las inversas en todos sus
    # registros/checkpoints, conservando deltas históricos de RNG del juego.
    def esquema_anterior(valor):
        if isinstance(valor, dict):
            return {k: esquema_anterior(v) for k,v in valor.items()
                    if k not in ('azar_estado_antes','azar_llamadas_antes')}
        if isinstance(valor, (list,tuple)):
            return [esquema_anterior(v) for v in valor]
        return valor
    ruta = str(tmp_path/'anterior-v4.bin')
    savegame.guardar(ruta, esquema_anterior(datos))
    otra = nueva_sesion(tmp_path, backend=backend_integrado(), log_ruta=None)
    otra.cargar_en_frio(ruta)
    assert otra.paso('deshacer')[0]
    assert estado_serializado(otra.estado)['azar_estado'] == antes['azar_estado']
    assert otra.estado.azar_llamadas == antes['azar_llamadas']


def test_intervalo_sin_azar_no_guarda_estado_completo_del_generador(tmp_path):
    backend = FakeBackend()
    for contenido in backend.fake._contenido.values():
        contenido.enemigos.clear()
        contenido.trampas.clear()
    ses = nueva_sesion(tmp_path, backend=backend)
    ses.iniciar(CRIPTA_ID)
    assert ses.paso('esperar')[0]
    inversa = next(iter(ses.fachada.pila))
    assert inversa['datos']['azar_llamadas_antes'] == 0
    assert 'azar_estado_antes' not in inversa['datos']
    assert ses.estado.azar_llamadas == 0
