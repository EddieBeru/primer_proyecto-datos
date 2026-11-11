"""FR-LIN-15/16: panel visual, foco, navegación y conservación de partida."""
import pygame
import pytest
from test_vista import app
from src.view.historia import ESPACIO, MARGEN, RADIO


def test_historia_foco_navegacion_y_cierre(app):
    for c in ('e','o','esperar'): assert app.ses.paso(c)[0]
    app.foto=app.ses.foto()
    antes=app.ses.estado.a_dict();log=app.ses._mem.leer()
    assert app.manejar_tecla(pygame.K_h)=='@historia-abrir'
    panel=app.panel_historia
    assert panel.resumen.accion==3
    app.manejar_tecla(pygame.K_LEFT)
    assert panel.resumen.accion==2
    app.actualizar_movimiento({pygame.K_w:True},10000)
    assert app.ses.estado.a_dict()==antes and app.ses._mem.leer()==log
    app.dibujar()
    assert panel.botones
    app.manejar_tecla(pygame.K_ESCAPE)
    assert app.panel_historia is None


def test_consulta_invalida_conserva_resumen_y_tokens(app):
    app.manejar_tecla(pygame.K_h);panel=app.panel_historia
    valido=panel.resumen
    panel.modo='tiempo';panel.entrada='999999';panel.consultar()
    assert panel.error and panel.resumen is valido
    assert all(v%8==0 for v in (ESPACIO,MARGEN,RADIO))


@pytest.mark.parametrize('tamano',[(640,480),(1024,800),(1280,720),(1920,1080)])
def test_panel_no_pierde_controles_en_tamanos_admitidos(app,tamano):
    app.redimensionar(tamano)
    app.manejar_tecla(pygame.K_h)
    app.dibujar()
    panel=app.panel_historia
    for rect,accion in panel.botones:
        assert app.ventana.get_rect().contains(rect),(tamano,accion,rect)
    # Clic de cierre sigue el mismo camino que Escape.
    rect=next(r for r,a in panel.botones if a=='cerrar')
    app.manejar_clic(rect.center)
    assert app.panel_historia is None


def test_eventos_de_texto_y_rueda_consumidos_por_panel(app):
    app.manejar_tecla(pygame.K_h);panel=app.panel_historia
    panel.activar('tiempo');panel.activar('entrada')
    app.manejar_evento(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_0,unicode='0',mod=0))
    assert panel.entrada=='0'
    app.manejar_evento(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN,unicode='',mod=0))
    assert not panel.error


def test_contenido_extenso_se_desplaza_sin_ocultar_controles(app):
    from dataclasses import replace
    app.manejar_tecla(pygame.K_h);panel=app.panel_historia
    panel.resumen=replace(panel.resumen,sala_nombre='Sala muy larga '*30,
        inventario=tuple('pocion_nombre_extenso_'+'x'*80 for _ in range(40)))
    app.dibujar()
    assert panel.scroll_max>0
    panel.scroll=panel.scroll_max
    app.dibujar()
    assert panel.scroll==panel.scroll_max
    assert any(a=='cerrar' for _,a in panel.botones)
