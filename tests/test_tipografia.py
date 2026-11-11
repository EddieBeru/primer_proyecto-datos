"""Métricas de los archivos distribuidos y acceso al texto completo."""
import os

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
import pytest

from src.view import paleta, texto
from src.view.medidas import medidas
from src.view.tipografia import DIRECTORIO, ESTILOS, VARIANTES, contraste, fuente


@pytest.mark.parametrize('peso', (400, 500, 600, 700))
def test_archivos_reales_y_digitos_tabulares(peso):
    pygame.font.init()
    assert (DIRECTORIO / f'Lato-{VARIANTES[peso]}.ttf').is_file()
    f = fuente(16, peso=peso)
    assert len({f.size(str(n))[0] for n in range(10)}) == 1
    archivo = pygame.font.Font(str(DIRECTORIO / f'Lato-{VARIANTES[peso]}.ttf'), 16)
    assert f.original.get_bold() == archivo.get_bold()
    assert f.size('Texto 0123456789') == archivo.size('Texto 0123456789')


@pytest.mark.parametrize('tamano', ((640, 480), (1024, 800), (1280, 720), (3840, 2160)))
def test_roles_legibles_y_lineas_sin_recorte(tamano):
    pygame.font.init()
    m = medidas(pygame.Surface(tamano))
    for rol, estilo in ESTILOS.items():
        f = m.estilo(rol)
        assert f.tamano >= estilo.tamano
        assert f.get_linesize() >= f.get_height()
        assert f.get_linesize() % 4 == 0
        assert f is m.estilo(rol)
        for cadena in ('Árbol · acción → 100/100', 'AVATAR 0123456789'):
            assert f.render(cadena, True, paleta.TEXTO).get_size() == f.size(cadena)


@pytest.mark.parametrize('frente', (paleta.TEXTO, paleta.SECUNDARIO, paleta.TEXTO_ACENTO))
@pytest.mark.parametrize('fondo', (paleta.PANEL, paleta.FONDO_APP, (252, 228, 198), (238, 228, 214)))
def test_contraste_texto_normal(frente, fondo):
    assert contraste(frente, fondo) >= 4.5


def test_contraste_accion_y_error():
    assert contraste(paleta.TEXTO_CLARO, paleta.ACCION) >= 4.5
    assert contraste(paleta.TEXTO_CLARO, (130, 48, 0)) >= 4.5
    assert contraste(paleta.TEXTO_CLARO, paleta.PELIGRO_FONDO) >= 4.5
    assert contraste(paleta.PELIGRO, paleta.PANEL) >= 4.5


def test_tooltip_completo_en_foco_y_scroll_dentro_de_ventana():
    pygame.font.init()
    sup = pygame.Surface((640, 480))
    f = medidas(sup).estilo('label')
    completo = 'Nombre muy largo con acentos y números 1234567890 ' * 100
    rect = pygame.Rect(560, 420, 56, 24)
    texto.iniciar_frame()
    assert texto.etiqueta(sup, f, completo, rect, paleta.TEXTO)
    texto.dibujar_ayuda(sup, foco=rect)
    assert texto._AYUDA_TEXTO == completo
    assert sup.get_rect().contains(texto._AYUDA_RECT)
    assert texto._AYUDA_MAX > 0
    assert texto.desplazar_ayuda(-10000, texto._AYUDA_RECT.center)
    assert texto._AYUDA_SCROLL == texto._AYUDA_MAX
    texto.iniciar_frame()
    texto.dibujar_ayuda(sup)
    assert texto._AYUDA_RECT is None


def test_envoltura_mas_estrecha_que_la_elipsis():
    pygame.font.init()
    f = fuente(14)
    assert texto.envolver('nombre extenso', f, 1, 1) == ['']


@pytest.mark.parametrize('original,esperado', (
    ('elige tu cripta', 'Elige tu cripta'),
    ('  (vacía)', '  (Vacía)'),
    ('área de ATQ', 'Área de ATQ'),
    ('F10 Ajustes', 'F10 Ajustes'),
    ('100/100', '100/100'),
    ('', ''),
))
def test_mayuscula_inicial_sin_perder_siglas(original, esperado):
    assert texto.inicial_mayuscula(original) == esperado


def test_objetos_y_tooltip_con_mayuscula_inicial():
    pygame.font.init()
    assert texto.etiqueta_item('itm_antorcha-01') == 'Antorcha'
    texto.iniciar_frame()
    sup = pygame.Surface((640, 480))
    f = medidas(sup).estilo('label')
    texto.etiqueta(sup,f,'nombre extenso',pygame.Rect(20,20,32,24),paleta.TEXTO)
    texto.dibujar_ayuda(sup,foco=pygame.Rect(20,20,32,24))
    assert texto._AYUDA_TEXTO == 'Nombre extenso'
    texto.iniciar_frame()
    texto.dibujar_ayuda(sup)


@pytest.mark.parametrize('titulo', ('Elige tu cripta', 'Versión anterior', 'Algo salió mal', 'CRIPTA'))
def test_titulo_proporcional_al_arte_sin_salto_a_fuente_de_boton(titulo):
    from src.view.pantallas import _fuente_titulo_caja, rect_caja_menu
    pygame.font.init()
    anteriores = None
    for tamano in ((640,480),(1024,800),(1920,1080),(3840,2160)):
        sup = pygame.Surface(tamano)
        rect = rect_caja_menu(sup)
        f = _fuente_titulo_caja(sup,titulo)
        assert f.size(titulo)[0] < rect.w
        proporcion = f.tamano / rect.h
        if anteriores:
            previo, razon = anteriores
            assert f.tamano > previo
            assert proporcion == pytest.approx(razon, rel=.12)
        anteriores = f.tamano, proporcion
