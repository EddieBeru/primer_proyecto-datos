"""C1-9: bitácora agrega al final, lee en orden, sin red."""

import pytest

from src.controller1.gamelog import Bitacora
from src.models.errors import BitacoraError


def test_anota_y_lee_en_orden(tmp_path):
    b = Bitacora(str(tmp_path / "juego.log"))
    b.anotar("t0 inicio")
    b.anotar("t1 norte")
    b.anotar("t2 atacar e1-1")
    assert b.leer() == ["t0 inicio", "t1 norte", "t2 atacar e1-1"]


def test_sin_archivo_lista_vacia(tmp_path):
    assert Bitacora(str(tmp_path / "nada.log")).leer() == []


def test_linea_invalida():
    import tempfile, os
    fd, ruta = tempfile.mkstemp()
    os.close(fd)
    b = Bitacora(ruta)
    for mala in ("", "   ", None, 42):
        with pytest.raises(ValueError):
            b.anotar(mala)
    assert b.leer() == []
    os.remove(ruta)


def test_corrupta_lanza_error_propio(tmp_path):
    ruta = str(tmp_path / "juego.log")
    with open(ruta, "wb") as f:
        f.write(b"\xff\xfe\x00binario")
    with pytest.raises(BitacoraError):
        Bitacora(ruta).leer()


def test_nunca_sobrescribe(tmp_path):
    ruta = str(tmp_path / "juego.log")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("vieja\n")
    b = Bitacora(ruta)
    b.anotar("nueva")
    assert b.leer() == ["vieja", "nueva"]


@pytest.mark.parametrize('linea', ['#ir-a', '#ir-a 2 extra', '#ir-a x', '#ir-a 2.0', '#ir-a  2', '#otra 2'])
def test_comentario_viaje_rechaza_corrupcion(linea):
    from src.controller2.bitacora import BitacoraMemoria
    b = BitacoraMemoria()
    with pytest.raises(ValueError):
        b.anotar(linea)
    assert b.leer() == []


def test_comentario_viaje_estricto_y_header():
    from src.controller2.bitacora import BitacoraMemoria, parsear
    b = BitacoraMemoria()
    b.anotar('#ir-a -12')
    assert parsear(b.leer()[0]) == {'comentario': 'ir-a', 'destino': -12}
    with pytest.raises(ValueError):
        b.anotar('#cripta incompleto')


def test_reproductor_c2_ignora_comentario_sin_iniciar_viaje():
    from src.controller2.bitacora import reproducir
    class FachadaFalsa:
        def __init__(self):
            self.movimientos = []
        def mover(self, direccion):
            self.movimientos.append(direccion)
    f = FachadaFalsa()
    reproducir(f, ['#ir-a 12', '0|mover|jugador|E'])
    assert f.movimientos == ['E']
