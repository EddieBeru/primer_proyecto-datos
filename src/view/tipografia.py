"""Roles tipográficos reales: tamaño, peso, interlineado y tracking medidos."""
from dataclasses import dataclass
from pathlib import Path
import math
import pygame

DIRECTORIO = Path(__file__).resolve().parents[2] / 'assets' / 'fonts'
VARIANTES = {400: 'Regular', 500: 'Medium', 600: 'Semibold', 700: 'Bold'}


@dataclass(frozen=True)
class Estilo:
    tamano: int
    peso: int
    linea: int
    tracking: float = 0


ESTILOS = {
    'h1': Estilo(28, 700, 36, -.02),
    'h2': Estilo(20, 600, 28, -.01),
    'h3': Estilo(16, 600, 24),
    'cuerpo': Estilo(16, 400, 24),
    'datos': Estilo(16, 400, 24),
    'boton': Estilo(14, 600, 20, .01),
    'label': Estilo(14, 500, 20),
    'auxiliar': Estilo(12, 400, 16, .02),
}
_CACHE = {}


class FuenteUI:
    """API de Font usada por la vista, con tracking explícito y métricas iguales al dibujo."""
    def __init__(self, tamano, peso, linea, tracking):
        self.tamano, self.peso = tamano, peso
        ruta = DIRECTORIO / f'Lato-{VARIANTES[peso]}.ttf'
        self.original = (pygame.font.Font(str(ruta), tamano) if ruta.is_file() else
                         pygame.font.SysFont('segoeui,dejavusans,liberationsans', tamano,
                                             bold=peso == 700))
        self.linea = math.ceil(max(linea, self.original.get_height()) / 4) * 4
        self.tracking = tracking * tamano

    def size(self, cadena):
        cadena = str(cadena)
        if not self.tracking or len(cadena) < 2:
            return self.original.size(cadena)
        ancho = sum(self.original.size(c)[0] for c in cadena) + self.tracking * (len(cadena)-1)
        return max(0, math.ceil(ancho)), self.original.get_height()

    def render(self, cadena, antialias, color, background=None):
        cadena = str(cadena)
        if not self.tracking or len(cadena) < 2:
            return self.original.render(cadena, antialias, color, background)
        ancho, alto = self.size(cadena)
        superficie = pygame.Surface((max(1, ancho), alto), pygame.SRCALPHA)
        if background is not None: superficie.fill(background)
        x = 0.0
        for c in cadena:
            imagen = self.original.render(c, antialias, color)
            superficie.blit(imagen, (round(x), 0))
            x += self.original.size(c)[0] + self.tracking
        return superficie

    def get_height(self): return self.original.get_height()
    def get_linesize(self): return self.linea
    def get_bold(self): return self.peso == 700
    def metrics(self, texto): return self.original.metrics(texto)
    def get_ascent(self): return self.original.get_ascent()
    def get_descent(self): return self.original.get_descent()


def fuente(tamano=16, negrita=False, *, peso=None, factor=1.0, rol=None):
    if rol is not None:
        estilo = ESTILOS[rol]
        tamano, peso, linea, tracking = estilo.tamano, estilo.peso, estilo.linea, estilo.tracking
    else:
        peso = peso or (700 if negrita and tamano >= 24 else 600 if negrita else 400)
        tracking = -.02 if tamano >= 24 else -.01 if negrita and tamano >= 18 else .02 if tamano <= 12 else 0
        linea = tamano * (1.5 if 14 <= tamano <= 16 else 1.3)
    if peso not in VARIANTES: raise ValueError('Peso tipográfico admitido:400/500/600/700')
    escala = max(1.0, factor)
    tamano = max(11, round(tamano * escala))
    clave = (tamano, peso, math.ceil(linea*escala/4)*4, tracking)
    if clave not in _CACHE: _CACHE[clave] = FuenteUI(*clave)
    return _CACHE[clave]


def contraste(frente, fondo):
    def luminancia(color):
        canales = [v/255 for v in color[:3]]
        canales = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in canales]
        return .2126*canales[0]+.7152*canales[1]+.0722*canales[2]
    a,b = luminancia(frente),luminancia(fondo)
    return (max(a,b)+.05)/(min(a,b)+.05)
