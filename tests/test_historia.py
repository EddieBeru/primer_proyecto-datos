"""FR-LIN-01–07/11/12: consultas, retroceso y persistencia en Sesión."""
import pytest
from test_sesion import nueva_sesion, CRIPTA_ID
from src.controller1 import savegame
from src.models.errors import GuardadoError


def sesion(tmp_path,k=2):
    s=nueva_sesion(tmp_path,checkpoint_cada=k);s.iniciar(CRIPTA_ID,semilla=23)
    s.estado.jugador.vida_max=s.estado.jugador.vida_actual=1000
    return s


def test_historia_consulta_pura_y_ordinal(tmp_path):
    s=sesion(tmp_path)
    for c in ('e','o','esperar'):
        assert s.paso(c)[0]
    actual=s.estado.a_dict(); log=s._mem.leer(); historia=s.linea.a_dict()
    assert s.historia_accion(1).sala_id==1
    assert s.historia_accion(2).sala_id==2
    assert s.historia(0).sala_id==1
    assert s.historia(100).sala_id==2
    assert s.paso('historia #2')[0]
    assert s.estado.a_dict()==actual and s._mem.leer()==log and s.linea.a_dict()==historia
    for t in (-1,s.estado.reloj+1,True,'a'):
        with pytest.raises(ValueError): s.historia(t)
    for k in (0,100,True):
        with pytest.raises(ValueError): s.historia_accion(k)


def test_guardado_historia_roundtrip_y_rechazo_anteriores(tmp_path):
    s=sesion(tmp_path)
    for c in ('s','s','n'): assert s.paso(c)[0]
    esperado=[s.historia_accion(i) for i in range(1,4)]
    ruta=str(tmp_path/'v4.bin');s.guardar(ruta)
    assert (tmp_path/'v4.bin').read_bytes()[len(savegame.MAGIA)]==4
    assert savegame.cargar_sala(ruta,1)['id']==1
    s.cargar(ruta)
    assert [s.historia_accion(i) for i in range(1,4)]==esperado
    s2=sesion(tmp_path);s2.cargar_en_frio(ruta)
    assert s2.historia_accion(2)==esperado[1]
    viejo=str(tmp_path/'v3.bin');savegame.guardar(viejo,s.estado.a_dict())
    actual=s.estado.a_dict()
    with pytest.raises(GuardadoError,match='v4'): s.cargar(viejo)
    assert s.estado.a_dict()==actual


def test_deshacer_elimina_rama_y_registra_pergamino(tmp_path):
    s=sesion(tmp_path)
    s.estado.jugador.inventario.extend(['pergamino-01']*3)
    for c in ('e','o','esperar'): assert s.paso(c)[0]
    assert s.paso('deshacer')[0]
    assert len(s.linea.acciones)==3 and s.linea.acciones[-1][2]=='deshacer'
    assert s.historia_accion(3).reloj==s.estado.reloj
    assert s.paso('deshacer')[0]
    assert len(s.linea.acciones)==2
    assert s.paso('esperar')[0]
    assert len(s.linea.acciones)==3
    s.guardar(str(tmp_path/'undo.bin'));s.cargar(str(tmp_path/'undo.bin'))


def test_historia_replay_no_confunde_turnos_enemigos(tmp_path):
    s=sesion(tmp_path)
    # Sin cambios de fixture externos, para equivalencia con replay.
    s=nueva_sesion(tmp_path,checkpoint_cada=2);s.iniciar(CRIPTA_ID,semilla=23)
    for c in ('e','esperar','o'): assert s.paso(c)[0]
    otro=nueva_sesion(tmp_path,log_ruta=None,checkpoint_cada=2)
    r=otro.reproducir(str(tmp_path/'p.log'),hasta=100)
    assert r==s.historia(100)
    assert otro.historia_accion(2)==s.historia_accion(2)


def test_fallo_del_registrador_revierte_intervalo_sin_snapshot(tmp_path,monkeypatch):
    s=sesion(tmp_path)
    assert s.paso('e')[0]
    antes=s.estado.a_dict();linea=s.linea.a_dict();log=s._mem.leer()
    def fallo(*args): raise RuntimeError('fallo inyectado')
    monkeypatch.setattr(s.linea,'cerrar_accion',fallo)
    ok,msg,_=s.paso('o')
    assert not ok and 'registrar' in msg
    from src.controller2.registro_mutaciones import dato
    assert dato(s.estado.a_dict())==dato(antes)
    assert s.linea.a_dict()==linea and s._mem.leer()==log


def test_reconstruccion_completa_cubre_rng_eventos_agenda_y_entidades(tmp_path):
    from src.controller2.linea_tiempo import estado_serializado
    s=sesion(tmp_path,k=2)
    esperados=[]
    for comando in ('s','recoger llave-hierro-01','s','n','e','abrir N','n'):
        s.fachada._sync()
        esperados.append(estado_serializado(s.estado))
        assert s.paso(comando)[0]
    for i,esperado in enumerate(esperados):
        reconstruido=s.linea.reconstruir(s.linea.acciones[i][0])
        assert reconstruido==esperado


def test_carga_corrupta_conserva_historia_y_viaje(tmp_path):
    s=nueva_sesion(tmp_path,checkpoint_cada=2)
    for contenido in s.backend.fake._contenido.values(): contenido.enemigos.clear()
    s.iniciar(CRIPTA_ID);s.paso('e');s.paso('o')
    assert s.paso('ir a 2')[0]
    antes=s.estado.a_dict();historia=s.linea.a_dict()
    data=s.fachada.estado.a_dict();data['historia']=s.linea.a_dict()
    data['historia']['registros'][0][4]='corrupción'
    ruta=str(tmp_path/'corrupto.bin');savegame.guardar(ruta,data)
    with pytest.raises(GuardadoError):s.cargar(ruta)
    assert s.estado.a_dict()==antes and s.linea.a_dict()==historia and s.fachada.viaje.activo


def test_fallo_de_captura_no_muta_lista_o_partida(tmp_path,monkeypatch):
    s=sesion(tmp_path);s.paso('s')
    antes=s.estado.a_dict();linea=s.linea.a_dict()
    def fallo(*args):raise RuntimeError('captura indisponible')
    monkeypatch.setattr(s.linea,'registrar_cambio',fallo)
    ok,_,_=s.paso('recoger llave-hierro-01')
    assert not ok
    assert s.estado.a_dict()==antes and s.linea.a_dict()==linea


def test_fallo_al_cerrar_pergamino_preserva_rama_previa(tmp_path,monkeypatch):
    s=sesion(tmp_path);s.estado.jugador.inventario.append('pergamino-01')
    s.paso('e');s.paso('o')
    antes=s.estado.a_dict();linea=s.linea.a_dict()
    def fallo(*args):raise RuntimeError('cierre indisponible')
    monkeypatch.setattr(s.linea,'cerrar_accion',fallo)
    assert not s.paso('deshacer')[0]
    from src.controller2.registro_mutaciones import dato
    assert dato(s.estado.a_dict())==dato(antes) and s.linea.a_dict()==linea


def test_eventos_empatados_incluye_todos_y_consulta_futuro_rechaza(tmp_path):
    s=sesion(tmp_path)
    s.fachada.agenda.programar(25,'veneno',{'dano':3})
    s.fachada.agenda.programar(25,'quemadura',{'dano':4})
    assert s.paso('esperar')[0]
    r=s.historia(25)
    assert r.vida==993
    assert s.historia(24).vida==1000


def test_historia_antorcha_entrada_undo_y_guardado(tmp_path):
    s=sesion(tmp_path)
    s.proveedor.catalogo.update(s.backend.fake._fichas)
    s.estado.jugador.inventario.extend(['antorcha-01','pergamino-01'])
    assert s.paso('usar antorcha-01')[0]
    assert s.paso('s')[0]
    antes=s.historia_accion(2)
    actual=s.historia(s.estado.reloj)
    assert sum(f[2]=='explorada' for f in actual.mapa)>sum(f[2]=='explorada' for f in antes.mapa)
    assert s.paso('deshacer')[0]
    despues=s.historia(s.estado.reloj)
    assert despues.mapa==antes.mapa
    ruta=str(tmp_path/'antorcha.bin');s.guardar(ruta);s.cargar_en_frio(ruta)
    assert s.historia_accion(2).mapa==antes.mapa


def test_cada_paso_de_viaje_cuenta_y_undo_no_reanuda(tmp_path):
    s=nueva_sesion(tmp_path,checkpoint_cada=2)
    for contenido in s.backend.fake._contenido.values():
        contenido.enemigos.clear();contenido.trampas.clear()
    s.iniciar(CRIPTA_ID)
    s.estado.jugador.inventario.append('pergamino-01')
    for c in ('s','s','n','n'):assert s.paso(c)[0]
    assert s.paso('ir a 5')[0]
    n=len(s.linea.acciones)
    assert s.avanzar_viaje()[0] and len(s.linea.acciones)==n+1
    assert s.avanzar_viaje()[0] and len(s.linea.acciones)==n+2
    assert s.paso('deshacer')[0]
    assert not s.foto().viaje['activo'] and s.estado.sala_actual==3


def test_exito_sin_cambios_no_cuenta_ni_consume_tiempo(tmp_path):
    s=sesion(tmp_path)
    antes=s.estado.reloj;agenda=s.fachada.agenda.a_lista()
    assert s.paso('abrir E')[0]
    assert s.estado.reloj==antes and s.fachada.agenda.a_lista()==agenda
    assert not s.linea.acciones


@pytest.mark.parametrize('version',[1,2])
@pytest.mark.parametrize('en_frio',[False,True])
def test_guardados_p1_validos_rechazados_sin_modificar_sesion(tmp_path,version,en_frio):
    s=sesion(tmp_path);s.paso('e')
    ruta=str(tmp_path/f'p1-v{version}.bin')
    if version==1:
        from test_savegame import ESTADO
        savegame.guardar(ruta,ESTADO)
    else:
        datos=s.estado.a_dict();datos.pop('conocimiento')
        savegame.guardar(ruta,datos)
    actual=s.estado.a_dict();historia=s.linea.a_dict()
    cargar=s.cargar_en_frio if en_frio else s.cargar
    with pytest.raises(GuardadoError,match='incompatible'):cargar(ruta)
    assert s.estado.a_dict()==actual and s.linea.a_dict()==historia


def test_sync_segmentos_agenda_no_alias_y_fallo_atomico(tmp_path, monkeypatch):
    from src.controller2.registro_mutaciones import sincronizar_secuencia
    s = sesion(tmp_path)
    linea = s.linea
    linea.comenzar()
    antes = list(s.estado.agenda)
    nueva = [{'t': 0, 'seq': -2, 'tipo': 'turno', 'datos': {'actor': 'prueba'}}] + antes
    sincronizar_secuencia(s.estado, 'agenda', nueva, ordenada=True)
    nueva[0]['datos']['actor'] = 'mutado afuera'
    assert s.estado.agenda[0]['datos']['actor'] == 'prueba'
    assert linea.registros[-1][4][0]['datos']['actor'] == 'prueba'
    actual = s.estado.agenda
    registros = len(linea.registros)
    def fallar(*args):
        raise RuntimeError('fallo inyectado')
    monkeypatch.setattr(linea, 'registrar_cambio', fallar)
    with pytest.raises(RuntimeError, match='inyectado'):
        sincronizar_secuencia(s.estado, 'agenda', antes, ordenada=True)
    assert s.estado.agenda is actual
    assert len(linea.registros) == registros
