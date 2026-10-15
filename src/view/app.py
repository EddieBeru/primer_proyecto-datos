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
from src.view import capas, entrada, pantallas, ui
from src.view.sprites import SpriteManager

if TYPE_CHECKING:  # solo tipos
    from src.controller2.fachada import FotoEstado

FPS = 60
VELOCIDAD = 0.008  # fracción del área por frame (movimiento libre, solo vista)
AYUDA = ("WASD/flechas caminar libre · E abrir · Espacio atacar (cerca) · "
         "F recoger (cerca) · R usar · Enter equipar · Q soltar · Tab/U/T · "
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
        self.anim_pasos = 0  # frames restantes del paso visual (solo vista)
        self.tick_anim = 0  # reloj de la animación estilo Rojo/Azul
        self.tick_total = 0  # reloj global (parpadeo en reposo)
        self.pos_jugador = [0.5, 0.5]  # posición libre en la sala (solo vista)
        self.aviso: str | None = None  # toast local (no es foto.error)
        self.aviso_ttl = 0
        self.en_puerta = False  # evita re-disparar la puerta cada frame
        self.golpe: str | None = None  # instancia con destello de impacto
        self.golpe_ttl = 0

    # -- ciclo de vida (guía §1/§9) --
    def listar_para_seleccion(self, criptas: list, puede_continuar: bool) -> None:
        self.criptas = list(criptas)
        self.puede_continuar = puede_continuar
        self.pantalla = "seleccion" if criptas else "inicio"

    def _flip(self) -> None:
        """Vuelca el frame ya (la carga se pinta ANTES del bloqueo de red)."""
        pygame.event.pump()
        if self.ventana is pygame.display.get_surface():
            pygame.display.flip()

    def _pintar_carga(self, detalle: str = "Preparando la cripta…") -> None:
        """Pantalla de carga visible durante las peticiones de arranque."""
        self.pantalla = "carga"
        pantallas.pantalla_carga(self.ventana, self.fuente, detalle)
        self._flip()

    def iniciar_partida(self, cripta_id: str, semilla: int = 0) -> "FotoEstado":
        self._pintar_carga(f"Preparando {cripta_id}…")
        try:
            self.foto = self.ses.iniciar(cripta_id, semilla=semilla)
        except Exception:
            self.pantalla = "error"
            raise
        self._reset_vista()
        self.pantalla = "juego"
        return self.foto

    def cargar_partida(self, ruta: str | None = None) -> "FotoEstado":
        self._pintar_carga("Cargando partida…")
        try:
            self.foto = self.ses.cargar_en_frio(ruta or self.save_path)
        except Exception:
            self.pantalla = "error"
            raise
        self._reset_vista()
        self.pantalla = "juego"
        return self.foto

    def _reset_vista(self) -> None:
        self.facing = "N"
        self.sel_enemigo = self.sel_suelo = self.sel_inv = 0
        self.ref_vida = {}
        self.ultimo_error = None
        self.reporte = None
        self.anim_pasos = 0
        self.tick_anim = 0
        self.tick_total = 0
        self.pos_jugador = [0.5, 0.5]
        self.aviso = None
        self.aviso_ttl = 0
        self.en_puerta = False
        self.golpe = None
        self.golpe_ttl = 0
        self._memorizar_vida()

    def _memorizar_vida(self) -> None:
        """Primera vida vista por instancia (barras proporcionales, guía §8)."""
        if self.foto is None:
            return
        for e in self.foto.enemigos or []:
            inst = e.get("instancia", "")
            self.ref_vida[inst] = max(int(e.get("vida", 0)),
                                      self.ref_vida.get(inst, 0))

    def _pintar_cargando_sala(self) -> tuple[str | None, int]:
        """Píldora visible durante la petición de la sala destino.

        `ses.paso()` puede tardar 1-2 peticiones (+ waits 429): se pinta
        y vuelca un frame ANTES del bloqueo. Retorna el aviso previo para
        restaurarlo después (el pill no debe perdurar).
        """
        previo = (self.aviso, self.aviso_ttl)
        self.aviso, self.aviso_ttl = "Cargando sala…", 10 ** 6
        self.dibujar()
        self._flip()
        return previo

    # -- intenciones (guía §4/§5) --
    def enviar(self, texto: str) -> tuple[bool, str, "FotoEstado"]:
        """Manda una intención y refresca. Solo camino hacia `ses.paso()`."""
        assert self.foto is not None or texto, "inicia o carga primero"
        previo = None
        if self.foto is not None and self.pantalla == "juego" \
                and texto.strip().upper() in ("N", "S", "E", "O") \
                and len(texto.strip()) == 1:
            previo = self._pintar_cargando_sala()
        try:
            ok, msg, foto = self.ses.paso(texto)
        finally:
            if previo is not None:
                self.aviso, self.aviso_ttl = previo
        self.foto = foto
        self.ultimo_error = None if ok else msg
        if ok:
            direccion = texto.strip().upper()
            if direccion in ("N", "S", "E", "O"):
                self.facing = direccion
                self.anim_pasos = 8  # el personaje da el paso en pantalla
            partes = texto.strip().split()
            if len(partes) == 2 and partes[0].lower() == "atacar":
                self.golpe, self.golpe_ttl = partes[1], 12  # destello de impacto
            self._memorizar_vida()
            if foto.estado != "jugando":
                self.pantalla = "fin"
        return ok, msg, foto

    # -- movimiento libre y proximidad (solo vista; las reglas siguen en C2) --
    def _pos_px(self) -> tuple[float, float]:
        area = self.area_sala()
        return (area.x + self.pos_jugador[0] * area.w,
                area.y + self.pos_jugador[1] * area.h)

    def _avisar(self, texto: str, ttl: int = 90) -> None:
        self.aviso, self.aviso_ttl = texto, ttl

    def _paso_libre(self, direccion: str) -> str:
        """Mueve el sprite por la sala; solo cruza al llegar a puerta abierta.

        Caminar es gratis (no consume tiempo ni vida): los enemigos y efectos
        actúan tras tus intenciones (atacar, recoger, abrir, usar, esperar…).
        """
        vec = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "o": (-1, 0)}
        dx, dy = vec[direccion]
        self.pos_jugador[0] = min(0.96, max(0.04, self.pos_jugador[0] + dx * VELOCIDAD))
        self.pos_jugador[1] = min(0.96, max(0.04, self.pos_jugador[1] + dy * VELOCIDAD))
        self.facing = direccion.upper()
        self.anim_pasos = max(self.anim_pasos, 4)
        self.tick_anim += 1
        self._revisar_puerta()
        return "@paso"

    def _revisar_puerta(self) -> None:
        """Al pisar puerta abierta -> mover; cerrada -> aviso (E para abrir)."""
        if self.foto is None:
            return
        area = self.area_sala()
        jx, jy = self._pos_px()
        cerca = None
        for direccion in ("N", "S", "E", "O"):
            puerta = (self.foto.puertas or {}).get(direccion)
            if puerta is None:
                continue
            cx, cy = capas.rect_puerta(area, direccion).center
            if ((jx - cx) ** 2 + (jy - cy) ** 2) ** 0.5 <= capas.RADIO_PUERTA:
                cerca = (direccion, puerta)
                break
        if cerca is None:
            self.en_puerta = False
            return
        if self.en_puerta:
            return
        direccion, puerta = cerca
        if puerta.get("cerrada"):
            llave = puerta.get("llave")
            self._avisar("Puerta cerrada. Pulsa E" +
                         (f" (llave {llave})" if llave else ""))
            self.en_puerta = True
            return
        sala_antes = self.foto.sala_id
        ok, msg, _ = self.enviar(direccion)
        if ok and self.foto is not None and self.foto.sala_id != sala_antes:
            # Aparece en la puerta paralela (por donde entra), pegado al
            # marco. en_puerta=True evita recruzar al instante; al alejarse
            # del radio la bandera se limpia sola (cerca is None).
            entra = {"N": (0.5, 0.90), "S": (0.5, 0.10),
                     "E": (0.10, 0.5), "O": (0.90, 0.5)}
            self.pos_jugador = list(entra[direccion])
            self.en_puerta = True
        elif not ok:
            self._avisar(msg)
            self.en_puerta = True

    def _cercano(self, puntos: list[tuple[float, float, str]],
                 radio: int, que: str) -> str | None:
        """Id del punto más cercano en radio, o aviso local y None."""
        if self.foto is None:
            return None
        jx, jy = self._pos_px()
        mejor, mejor_d = None, float("inf")
        for x, y, ident in puntos:
            d = ((jx - x) ** 2 + (jy - y) ** 2) ** 0.5
            if d < mejor_d:
                mejor, mejor_d = ident, d
        if mejor is None or mejor_d > radio:
            self._avisar(f"Acércate {'al enemigo' if que == 'enemigo' else 'al objeto'}")
            return None
        return mejor

    def atacar_cercano(self) -> str | None:
        """Instancia enemiga a rango, o None con aviso (instancia, no tipo)."""
        area = self.area_sala()
        vivos = [e for e in (self.foto.enemigos or []) if e.get("vida", 0) > 0]
        puntos = [(c[0], c[1], e["instancia"])
                  for e, c in ((e, capas.pos_enemigo_animada(area, i, self.tick_total))
                               for i, e in enumerate(vivos))]
        objetivo = self._cercano(puntos, capas.RADIO_ENEMIGO, "enemigo")
        return f"atacar {objetivo}" if objetivo else None

    def recoger_cercano(self) -> str | None:
        """Id del suelo a rango, o None con aviso."""
        area = self.area_sala()
        suelo = list(self.foto.objetos_suelo or [])
        puntos = [(c[0], c[1], item)
                  for item, c in ((o, capas.pos_suelo(area, i)) for i, o in enumerate(suelo))]
        objetivo = self._cercano(puntos, capas.RADIO_OBJETO, "objeto")
        return f"recoger {objetivo}" if objetivo else None

    def manejar_tecla(self, key: int) -> str | None:
        """Tecla -> acción local o intención. Retorna lo ejecutado."""
        if self.pantalla == "juego" and self.foto is not None:
            direccion = entrada.mover_para_tecla(key)
            if direccion is not None:
                return self._paso_libre(direccion)
            if key == pygame.K_SPACE:
                accion = self.atacar_cercano()
                if accion is None:
                    return None
                ok, _, _ = self.enviar(accion)
                return accion if ok else None
            if key == pygame.K_f:
                accion = self.recoger_cercano()
                if accion is None:
                    return None
                ok, _, _ = self.enviar(accion)
                return accion if ok else None
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
            vec = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "O": (-1, 0)}
            dx, dy = vec.get(self.facing, (0, 0))
            desplaza = (dx * self.anim_pasos * 2, dy * self.anim_pasos * 2)
            moviendo = self.anim_pasos > 0
            if moviendo:
                self.anim_pasos -= 1
                self.tick_anim += 1
            self.tick_total += 1
            jx, jy = self._pos_px()
            area = self.area_sala()
            alcance = frozenset(
                e["instancia"] for i, e in enumerate(
                    [x for x in (self.foto.enemigos or []) if x.get("vida", 0) > 0])
                if ((jx - capas.pos_enemigo_animada(area, i, self.tick_total)[0]) ** 2
                    + (jy - capas.pos_enemigo_animada(area, i, self.tick_total)[1]) ** 2) ** 0.5
                <= capas.RADIO_ENEMIGO)
            pantallas.pantalla_juego(self.ventana, self.fuente, self.foto,
                                     self.sprites, self.area_sala(),
                                     self.sel_enemigo, self.sel_suelo, self.sel_inv,
                                     self.ref_vida, self.dev,
                                     self.facing, desplaza,
                                     (moviendo, self.tick_anim, self.tick_total),
                                     self._pos_px(), self.golpe, alcance)
            if self.golpe_ttl > 0:
                self.golpe_ttl -= 1
                if self.golpe_ttl == 0:
                    self.golpe = None
            if self.aviso and self.aviso_ttl > 0:
                ui.dibujar_toast(self.ventana, self.fuente, self.aviso)
                self.aviso_ttl -= 1
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
            if self.pantalla == "juego" and self.foto is not None:
                try:
                    held = pygame.key.get_pressed()
                    for tecla, direccion in entrada.MOVER.items():
                        if held[tecla]:
                            self._paso_libre(direccion)
                except Exception as e:
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
