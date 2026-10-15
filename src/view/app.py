"""App de vista Pygame (guía §1/§5 + Parte 1 §7): ventana, FPS y pantallas.

Solo habla con `Sesion`: intenciones via `ses.paso(texto)` y lectura de
`FotoEstado`. Nunca importa C1/C2 en runtime (ver checklist §12).
Loop oficial: intención -> foto (ya drenada) -> dibujar (guía §5).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pygame

from src.orchestrator.sesion import Sesion
from src.view import entrada, pantallas
from src.view.sprites import SpriteManager

if TYPE_CHECKING:  # solo tipos
    from src.controller2.fachada import FotoEstado

FPS = 60
AYUDA = ("WASD/flechas mover · E abrir · Espacio atacar · F recoger · "
         "R usar · Enter equipar · Q soltar · Tab/U/T · 1-8 enemigo · "
         "F1 dev · G guardar · Esc pausa")


class VistaApp:
    """Ventana Pygame sobre una Sesión ya creada (backend lo elige main)."""

    def __init__(self, sesion: Sesion, ancho: int = 960, alto: int = 640,
                 dev: bool = False, save_path: str = "partida.bin",
                 ventana: pygame.Surface | None = None) -> None:
        self.ses = sesion
        self.dev = dev
        self.save_path = save_path
        self.sprites = SpriteManager()
        pygame.font.init()
        self.fuente = pygame.font.SysFont("consolas,monospace", 16)
        self.ventana = ventana or pygame.display.set_mode((ancho, alto))
        pygame.display.set_caption("CRIPTA")
        self.reloj = pygame.time.Clock()
        self.pantalla = "inicio"
        self.foto: FotoEstado | None = None
        self.criptas: list = []
        self.puede_continuar = False
        self.facing = "N"
        self.sel_enemigo = 0
        self.sel_suelo = 0
        self.sel_inv = 0
        self.ref_vida: dict[str, int] = {}
        self.ultimo_error: str | None = None
        self.reporte: dict | None = None
        self.corriendo = True

    # -- ciclo de vida (guía §1/§9) --
    def listar_para_seleccion(self, criptas: list, puede_continuar: bool) -> None:
        self.criptas = list(criptas)
        self.puede_continuar = puede_continuar
        self.pantalla = "seleccion" if criptas else "inicio"

    def iniciar_partida(self, cripta_id: str, semilla: int = 0) -> "FotoEstado":
        self.pantalla = "carga"
        self.foto = self.ses.iniciar(cripta_id, semilla=semilla)
        self._reset_vista()
        self.pantalla = "juego"
        return self.foto

    def cargar_partida(self, ruta: str | None = None) -> "FotoEstado":
        self.foto = self.ses.cargar_en_frio(ruta or self.save_path)
        self._reset_vista()
        self.pantalla = "juego"
        return self.foto

    def _reset_vista(self) -> None:
        self.facing = "N"
        self.sel_enemigo = self.sel_suelo = self.sel_inv = 0
        self.ref_vida = {}
        self.ultimo_error = None
        self.reporte = None
        self._memorizar_vida()

    def _memorizar_vida(self) -> None:
        """Primera vida vista por instancia (barras proporcionales, guía §8)."""
        if self.foto is None:
            return
        for e in self.foto.enemigos or []:
            inst = e.get("instancia", "")
            self.ref_vida[inst] = max(int(e.get("vida", 0)),
                                      self.ref_vida.get(inst, 0))

    # -- intenciones (guía §4/§5) --
    def enviar(self, texto: str) -> tuple[bool, str, "FotoEstado"]:
        """Manda una intención y refresca. Solo camino hacia `ses.paso()`."""
        assert self.foto is not None or texto, "inicia o carga primero"
        ok, msg, foto = self.ses.paso(texto)
        self.foto = foto
        self.ultimo_error = None if ok else msg
        if ok:
            self._memorizar_vida()
            if foto.estado != "jugando":
                self.pantalla = "fin"
        return ok, msg, foto

    def manejar_tecla(self, key: int) -> str | None:
        """Tecla -> acción local o intención. Retorna lo ejecutado."""
        if self.pantalla == "juego" and self.foto is not None:
            direccion = entrada.mover_para_tecla(key)
            if direccion is not None:
                self.facing = direccion
            accion = entrada.intencion_para_tecla(
                key, self.foto, self.facing,
                self.sel_enemigo, self.sel_suelo, self.sel_inv)
            if accion is None:
                return None
            if accion.startswith("@"):
                return self._accion_local(accion)
            ok, _, _ = self.enviar(accion)
            return accion if ok else None
        if self.pantalla == "pausa":
            return self._tecla_pausa(key)
        if self.pantalla in ("inicio", "seleccion"):
            return self._tecla_menu(key)
        if self.pantalla in ("error", "version", "fin") and key == pygame.K_ESCAPE:
            self.pantalla = "inicio"
            return "@menu"
        return None

    def _accion_local(self, accion: str) -> str:
        if accion == "@pausa":
            self.pantalla = "pausa"
        elif accion == "@tab-inv":
            total = max(len(self.foto.inventario or []), 1)
            self.sel_inv = (self.sel_inv + 1) % total
        elif accion == "@tab-suelo":
            total = max(len(self.foto.objetos_suelo or []), 1)
            self.sel_suelo = (self.sel_suelo + 1) % total
        elif accion == "@dev":
            self.dev = not self.dev
        elif accion == "@guardar":
            self.guardar()
        elif accion.startswith("@enemigo+"):
            total = max(len([e for e in (self.foto.enemigos or [])
                             if e.get("vida", 0) > 0]), 1)
            self.sel_enemigo = int(accion.split("+")[1]) % total
        return accion

    def _tecla_pausa(self, key: int) -> str | None:
        if key == pygame.K_ESCAPE:
            self.pantalla = "juego"
            return "@volver"
        if key == pygame.K_g:
            self.guardar()
            return "@guardar"
        if key == pygame.K_c:
            try:
                self.cargar_partida()
                return "@cargar"
            except Exception as e:  # GuardadoError -> pantalla 1.7/1.6
                self.ultimo_error = str(e)
                self.pantalla = "version"
                return "@version"
        if key == pygame.K_q:
            self.pantalla = "inicio"
            return "@menu"
        return None

    def _tecla_menu(self, key: int) -> str | None:
        if self.pantalla == "inicio":
            if key == pygame.K_1:
                self.listar_para_seleccion(self.criptas, self.puede_continuar)
                return "@jugar"
            if key == pygame.K_2 and self.puede_continuar:
                try:
                    self.cargar_partida()
                    return "@cargar"
                except Exception as e:
                    self.ultimo_error = str(e)
                    self.pantalla = "version"
                    return "@version"
            if key == pygame.K_3:
                self.corriendo = False
                return "@salir"
        elif self.pantalla == "seleccion":
            idx = key - pygame.K_1 if pygame.K_1 <= key <= pygame.K_9 else None
            if idx is not None and 0 <= idx < len(self.criptas):
                crip = self.criptas[idx]
                cid = crip.get("id", crip.get("cripta_id", "")) if isinstance(crip, dict) else crip.id
                self.iniciar_partida(str(cid))
                return "@jugar"
            if key == pygame.K_ESCAPE:
                self.pantalla = "inicio"
                return "@menu"
        return None

    # -- persistencia y fin (guía §9; la vista no toca archivos) --
    def guardar(self, ruta: str | None = None) -> None:
        self.ses.guardar(ruta or self.save_path)

    def finalizar(self) -> dict:
        self.reporte = self.ses.finalizar()
        return self.reporte

    # -- dibujo (Parte 1 §2/§7) --
    def area_sala(self) -> pygame.Rect:
        w, h = self.ventana.get_size()
        return pygame.Rect(10, 36, min(620, w - 240), h - 200)

    def dibujar(self) -> None:
        if self.pantalla == "inicio":
            pantallas.pantalla_inicio(self.ventana, self.fuente, self.puede_continuar)
        elif self.pantalla == "seleccion":
            pantallas.pantalla_seleccion(self.ventana, self.fuente, self.criptas)
        elif self.pantalla == "carga":
            pantallas.pantalla_carga(self.ventana, self.fuente)
        elif self.pantalla == "pausa":
            pantallas.menu_pausa(self.ventana, self.fuente)
        elif self.pantalla == "fin" and self.foto is not None:
            if self.reporte is None and self.foto.estado != "jugando":
                self.finalizar()
            pantallas.pantalla_fin(self.ventana, self.fuente, self.foto, self.reporte)
        elif self.pantalla == "error":
            pantallas.pantalla_error(self.ventana, self.fuente, self.ultimo_error or "")
        elif self.pantalla == "version":
            pantallas.pantalla_version(self.ventana, self.fuente, self.ultimo_error or "")
        elif self.foto is not None:
            pantallas.pantalla_juego(self.ventana, self.fuente, self.foto,
                                     self.sprites, self.area_sala(),
                                     self.sel_enemigo, self.sel_suelo, self.sel_inv,
                                     self.ref_vida, self.dev)
        pygame.display.flip() if self.ventana is pygame.display.get_surface() else None

    def ejecutar(self) -> int:
        """Bucle real: leer teclas -> Sesión -> dibujar -> FPS (Parte 1 §7)."""
        while self.corriendo:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.corriendo = False
                elif evento.type == pygame.KEYDOWN:
                    try:
                        self.manejar_tecla(evento.key)
                    except Exception as e:  # nunca crashear la ventana
                        self.ultimo_error = str(e)
                        self.pantalla = "error"
            try:
                self.dibujar()
            except Exception as e:
                self.ultimo_error = str(e)
                self.pantalla = "error"
            self.reloj.tick(FPS)
        return 0


def rutas_log_por_defecto() -> tuple[str, str]:
    """Rutas recomendadas (guía §1: siempre log_ruta en juego real)."""
    base = os.path.join(os.getcwd(), "partida")
    return base + ".log", base + ".bin"
