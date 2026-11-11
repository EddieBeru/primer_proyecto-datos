"""FR-LIN-06/08: configuración y replay textual sin instanciar vista."""
import pytest
from src.controller1.cli import parse_args
from src.main import main
from test_sesion import nueva_sesion, CRIPTA_ID


@pytest.mark.parametrize('argumentos',[['--checkpoint-cada','0'],['--checkpoint-cada','-2'],['--hasta','1'],['--replay','x','--hasta','-1']])
def test_argumentos_invalidos(argumentos):
    with pytest.raises(SystemExit):parse_args(argumentos)


def test_configuracion_y_replay_hasta(tmp_path,capsys,monkeypatch):
    s=nueva_sesion(tmp_path);s.iniciar(CRIPTA_ID)
    assert s.paso('e')[0]
    import src.main as entrada
    monkeypatch.setattr(entrada,'_nueva_sesion',lambda *a,**kw:nueva_sesion(tmp_path,log_ruta=None))
    assert main(['--replay',str(tmp_path/'p.log'),'--hasta','99999','--checkpoint-cada','10'])==0
    salida=capsys.readouterr().out
    assert 'Historia' in salida and 'terminó antes' in salida
    assert parse_args(['--checkpoint-cada','50']).checkpoint_cada==50
