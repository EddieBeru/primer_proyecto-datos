"""FR-LIN-04/08/09/10/11: diario independiente del undo P1."""
import copy
import pytest
from src.controller2.linea_tiempo import LineaTiempo, aplicar
from src.controller2.modelo import EstadoPartida, JugadorVivo, SalaViva


def estado():
    e=EstadoPartida('c','1','1',1,9,'k',20,JugadorVivo(100,100,5,2,100))
    e.registrar_sala(SalaViva(1,'Origen'))
    return e


@pytest.mark.parametrize('k',[0,-1,True,1.5,'20'])
def test_k_invalido(k):
    with pytest.raises(ValueError): LineaTiempo(estado(),k)


def test_diario_y_checkpoint_sin_snapshot_por_accion():
    e=estado(); l=LineaTiempo(e,2)
    for i in range(5):
        l.comenzar(); e.jugador.vida_actual-=1; e.reloj+=100
        l.evento(); l.cerrar_accion({'reloj':i*100},e)
    assert len(l.checkpoints)==3
    assert l.reconstruir(l.acciones[2][0])['jugador']['vida_actual']==98
    assert l.reconstruir(0)['jugador']['vida_actual']==100
    actual=copy.deepcopy(e.a_dict());l.reconstruir(0)
    assert e.a_dict()==actual
    rec=LineaTiempo.desde_dict(l.a_dict(),e)
    assert rec.a_dict()==l.a_dict()


def test_delta_captura_lista_y_mapa_anidados():
    e=estado(); l=LineaTiempo(e,2);l.comenzar()
    e.jugador.inventario.append('pergamino')
    e.jugador.efectos['veneno']=3
    e.salas[1].objetos_suelo.extend(['llave','pocion'])
    l.cerrar_accion({'reloj':0},e)
    anterior=l.reconstruir(0)
    assert anterior['jugador']['inventario']==[]
    assert anterior['jugador']['efectos']=={}
    assert anterior['salas']['1']['objetos_suelo']==[]


def test_carga_rechaza_checkpoint_incoherente():
    e=estado();l=LineaTiempo(e);d=l.a_dict();d['checkpoints'][0][2]['jugador']['vida_actual']=1
    with pytest.raises(ValueError): LineaTiempo.desde_dict(d,e)


@pytest.mark.parametrize('corrupcion',['k','corte','tiempo','offset','tipo','version','delta'])
def test_corrupcion_estructural(corrupcion):
    e=estado();l=LineaTiempo(e,1);l.comenzar();e.jugador.vida_actual=99;e.reloj=100;l.evento();l.cerrar_accion({'reloj':0},e)
    d=l.a_dict()
    if corrupcion=='k':d['k']=True
    elif corrupcion=='corte':d['acciones'][0][0]=9999
    elif corrupcion=='tiempo':d['cortes'][0][0]=-1
    elif corrupcion=='offset':d['checkpoints'][1][0]=0
    elif corrupcion=='tipo':d['acciones'][0][2]='volar'
    elif corrupcion=='version':d['version']=True
    else:d['registros'][0][3]='si'
    with pytest.raises((ValueError,TypeError,IndexError)):LineaTiempo.desde_dict(d,e)


def test_numero_de_intervalos_reconstruidos_no_supera_k():
    from src.orchestrator.bench_historia import carga
    for k in (1,2,5):
        linea=carga(k,acciones=21)
        for t in range(0,2101,25):
            linea.consultar(t=t)
            assert linea.ultimas_acciones<=k
