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
from src.view import capas, entrada, paleta, pantallas, ui
from src.view.sfx import Sonidos
from src.view.sprites import SpriteManager

if TYPE_CHECKING:  # solo tipos
    from src.controller2.fachada import FotoEstado

FPS = 60
VELOCIDAD = 0.008  # fracción del área por frame (movimiento libre, solo vista)
VECTOR_DIRECCION = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "o": (-1, 0)}
AYUDA = ("WASD/flechas caminar libre · E abrir · Espacio atacar (cerca) · "
         "F recoger (cerca) · R usar · Enter equipar · Q soltar · Tab/U/T · "
         "pisar trampas las dispara · F1 dev · G guardar · Esc pausa")


class VistaApp:
    """Ventana Pygame sobre una Sesión ya creada (backend lo elige main)."""

    def __init__(self, sesion: Sesion, ancho: int = 960, alto: int = 640,
                 dev: bool = False, save_path: str = "partida.bin",
                 ventana: pygame.Surface | None = None) -> None:
        self.ses = sesion
        self.dev = dev
        self.save_path = save_path
        self.sprites = SpriteManager()
        self.sfx = Sonidos()  # solo audio local: nunca rompe la partida
        pygame.font.init()
        self.fuente = pygame.font.SysFont("consolas,monospace", 16)
        self.ventana = ventana or pygame.display.set_mode((ancho, alto))
        pygame.display.set_caption("CRIPTA")
        pygame.display.set_icon(self.sprites.icono())  # el prota de paso
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
        self.memoria_spots: dict = {}  # (sala, tipo, id) -> puesto estable
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
        self.dano_ttl = 0  # destello rojo al perder vida (mejoras 2026-10)
        self.trampa_pisada: str | None = None  # no repetir mientras siga encima
        self.ataque_ttl = 0  # feedback de ataque (embestida; con arma + estela)
        self.ataque_dir = "N"  # dirección del golpe (facing al atacar)
        self.ataque_espada = False  # True = además estela (la embestida va siempre)
        self.espejo = False  # arte volteado (mira a la izquierda); se conserva
        self.paso_dir = (0.0, 0.0)  # dirección del paso visible actual
        self.paso_push = [0.0, 0.0]  # desplazamiento del paso, suavizado
        self.trampas_fuego = {}  # {instancia: ttl} trampas recién disparadas

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
        self.memoria_spots = {}  # partida nueva: scatter reproducible
        self.pantalla = "juego"
        self.sfx.jingle_inicio()  # guiño: suena cada vez que empieza la partida
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
        self.sfx.jingle_inicio()  # guiño también al retomar una partida
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
        self.dano_ttl = 0
        self.trampa_pisada = None
        self.ataque_ttl = 0
        self.ataque_dir = "N"
        self.ataque_espada = False
        self.espejo = False
        self.paso_dir = (0.0, 0.0)
        self.paso_push = [0.0, 0.0]
        self.trampas_fuego = {}
        self._memorizar_vida()

    def _memorizar_vida(self) -> None:
        """Primera vida vista por instancia (barras proporcionales, guía §8)."""
        if self.foto is None:
            return
        for e in self.foto.enemigos or []:
            inst = e.get("instancia", "")
            self.ref_vida[inst] = max(int(e.get("vida", 0)),
                                      self.ref_vida.get(inst, 0))

    def _fases_trampas(self) -> dict[str, float]:
        """{instancia: fase 0..1} de las trampas que están chispeando."""
        return {inst: ttl / 12 for inst, ttl in self.trampas_fuego.items()}

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
        sala_antes = self.foto.sala_id if self.foto is not None else None
        try:
            vida_antes = int(self.foto.jugador.get("vida", 0)) if self.foto is not None else None
        except Exception:
            vida_antes = None
        previo = None
        if self.foto is not None and self.pantalla == "juego" \
                and texto.strip().upper() in ("N", "S", "E", "O") \
                and len(texto.strip()) == 1:
            previo = self._pintar_cargando_sala()
        mensajes_antes = list(self.foto.mensajes or []) if self.foto is not None else []
        try:
            ok, msg, foto = self.ses.paso(texto)
        finally:
            if previo is not None:
                self.aviso, self.aviso_ttl = previo
        self.foto = foto
        self.ultimo_error = None if ok else msg
        if ok:
            # Chispazo: el motor anota `efecto|trampa|<inst>` en la bitácora
            # (entrada por §2.10 o pisar); el multiset contra la foto previa
            # detecta las recién disparadas aunque ya se hayan rearmado.
            restantes = list(mensajes_antes)
            nuevos = []
            for m in (foto.mensajes or []):
                if m in restantes:
                    restantes.remove(m)
                else:
                    nuevos.append(m)
            self.trampas_fuego = {str(m).rsplit("|", 1)[-1]: 12
                                  for m in nuevos if "|efecto|trampa|" in str(m)}
            direccion = texto.strip().upper()
            if direccion in ("N", "S", "E", "O"):
                self.facing = direccion
                if direccion in ("E", "O"):
                    self.espejo = direccion == "O"
                self.paso_dir = {"N": (0.0, -1.0), "S": (0.0, 1.0),
                                 "E": (1.0, 0.0), "O": (-1.0, 0.0)}[direccion]
                self.anim_pasos = 8  # el personaje da el paso en pantalla
            partes = texto.strip().split()
            if len(partes) == 2 and partes[0].lower() == "atacar":
                self.golpe, self.golpe_ttl = partes[1], 12  # destello de impacto
                # Feedback de ataque: embestida siempre (con o sin arma);
                # con arma se añade ADEMÁS la estela de espada.
                self.ataque_ttl, self.ataque_dir = 12, self.facing
                self.ataque_espada = capas.arma_visible(foto)
            # Mejoras 2026-10: feedback visible al perder vida (trampas,
            # contraataques, veneno/quemadura…).
            try:
                vida_ahora = int(foto.jugador.get("vida", 0))
            except Exception:
                vida_ahora = None
            if vida_antes is not None and vida_ahora is not None and vida_ahora < vida_antes:
                self.dano_ttl = 14
                if partes and partes[0].lower() == "pisar" and msg:
                    self._avisar(msg)
                elif self.trampas_fuego and sala_antes is not None \
                        and foto.sala_id != sala_antes:
                    # §2.10: la trampa se activa al ENTRAR a la sala, sin
                    # importar la distancia; el chispazo marca el origen.
                    plural = "s" if len(self.trampas_fuego) > 1 else ""
                    self._avisar(f"¡Trampa{plural} al entrar! "
                                 f"−{vida_antes - vida_ahora} de vida")
                else:
                    self._avisar(f"¡{vida_antes - vida_ahora} de daño!")
            # Mejoras 2026-10: al entrar a una sala oscura sin antorcha.
            if sala_antes is not None and foto.sala_id != sala_antes \
                    and getattr(foto, "sala_oscura", False) \
                    and not capas.antorcha_encendida(foto):
                self._avisar("Sala oscura: usa una antorcha (R)", ttl=150)
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
        """Mueve el sprite por la sala; solo cruza al llegar a puerta abierta."""
        dx, dy = VECTOR_DIRECCION[direccion]
        return self._mover_libre(dx, dy)

    def _mover_libre(self, dx: float, dy: float) -> str:
        """Aplica el vector de paso normalizado (diagonal = recto).

        Caminar es gratis (no consume tiempo ni vida): los enemigos y efectos
        actúan tras tus intenciones (atacar, recoger, abrir, usar, esperar…).
        El vector llega en unidades de eje (p. ej. (1, 1) en diagonal) y se
        normaliza para que ninguna dirección sea más rápida que otra; (0, 0)
        (teclas opuestas) no mueve.
        """
        largo = (dx * dx + dy * dy) ** 0.5
        if largo == 0:
            return "@paso"
        dx, dy = dx / largo, dy / largo
        self.pos_jugador[0] = min(0.96, max(0.04, self.pos_jugador[0] + dx * VELOCIDAD))
        self.pos_jugador[1] = min(0.96, max(0.04, self.pos_jugador[1] + dy * VELOCIDAD))
        if dx and not dy:
            self.facing = "E" if dx > 0 else "O"
        elif dy and not dx:
            self.facing = "S" if dy > 0 else "N"
        if dx:  # el volteo horizontal solo depende del eje X: se conserva
            self.espejo = dx < 0  # al subir/bajar (no voltea "de la nada")
        self.paso_dir = (dx, dy)  # paso visible hacia donde se camina
        self.anim_pasos = max(self.anim_pasos, 4)
        self.tick_anim += 1
        self._revisar_puerta()
        self._revisar_trampas()
        return "@paso"

    def _empuje_ataque(self) -> tuple[int, int]:
        """Embestida hacia la dirección del golpe mientras dure el ataque.

        Se dibuja SIEMPRE que haya ataque activo, con o sin arma (con arma
        se suma a la estela); es solo desplazamiento visual del App, sin
        tocar el modelo ni el contrato K5.
        """
        if self.ataque_ttl <= 0:
            return (0, 0)
        adx, ady = VECTOR_DIRECCION.get(str(self.ataque_dir).lower(), (0, 0))
        empuje = round(11 * self.ataque_ttl / 12)
        return (adx * empuje, ady * empuje)

    def _revisar_trampas(self) -> None:
        """Pasar por encima de una trampa armada la dispara (mejoras 2026-10).

        El motor ya dispara las trampas al entrar a la sala (§2.10); esto
        cubre las que se rearman mientras caminas dentro de la sala. La
        intención `pisar <instancia>` respeta armada/rearme/deshacer. Una
        misma trampa no se repite mientras sigas parado encima: hay que
        salir del radio y volver a pisarla.
        """
        if self.foto is None:
            return
        _, puntos = self._spots()
        jx, jy = self._pos_px()
        cerca = set()
        for i, trampa in enumerate(self.foto.trampas or []):
            if i >= len(puntos):
                break
            cx, cy = puntos[i]
            if ((jx - cx) ** 2 + (jy - cy) ** 2) ** 0.5 <= capas.RADIO_TRAMPA:
                cerca.add(trampa.get("instancia", ""))
        if self.trampa_pisada not in cerca:
            self.trampa_pisada = None
        for i, trampa in enumerate(self.foto.trampas or []):
            if i >= len(puntos) or not trampa.get("armada", True):
                continue
            inst = trampa.get("instancia", "")
            if inst in cerca and inst != self.trampa_pisada:
                self.trampa_pisada = inst
                self.enviar(f"pisar {inst}")
                break

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

    def _spots(self) -> tuple[list, list]:
        """Puestos (items, trampas) estables de la sala actual."""
        if self.foto is None:
            return [], []
        return capas.asignar_spots(
            self.area_sala(), self.foto.sala_id,
            list(self.foto.trampas or []),
            list(self.foto.objetos_suelo or []),
            self.memoria_spots)

    def recoger_cercano(self) -> str | None:
        """Id del suelo a rango, o None con aviso."""
        suelo = list(self.foto.objetos_suelo or [])
        puntos_items, _ = self._spots()
        puntos = [(c[0], c[1], item)
                  for item, c in zip(suelo, puntos_items)]
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
            # Desplazamiento del paso con suavizado: al girar no salta de eje
            # (el objetivo es corto, ~8 px; el push lo alcanza en 2-3 frames).
            objetivo = (self.paso_dir[0] * self.anim_pasos * 2,
                        self.paso_dir[1] * self.anim_pasos * 2)
            self.paso_push[0] += (objetivo[0] - self.paso_push[0]) * 0.5
            self.paso_push[1] += (objetivo[1] - self.paso_push[1]) * 0.5
            desplaza = (round(self.paso_push[0]), round(self.paso_push[1]))
            empuje = self._empuje_ataque()
            if empuje != (0, 0):
                # Embestida al atacar (con o sin arma): con arma se suma a
                # la estela para que la acción se lea igual de claro.
                desplaza = (desplaza[0] + empuje[0], desplaza[1] + empuje[1])
            if self.dano_ttl > 0:
                # Sacudida breve al recibir daño (patrón fijo, sin azar real).
                sac = ((-3, 2), (3, -2), (-2, -2), (2, 2),
                       (-1, 3), (1, -3))[self.dano_ttl % 6]
                desplaza = (desplaza[0] + sac[0], desplaza[1] + sac[1])
            tajo = (self.ataque_dir, self.ataque_ttl / 12) \
                if self.ataque_ttl > 0 and self.ataque_espada else None
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
                                     self._pos_px(), self.golpe, alcance,
                                     spots=self._spots(),
                                     tinte_dano=self.dano_ttl > 0, tajo=tajo,
                                     espejo=self.espejo,
                                     trampas_fuego=self._fases_trampas())
            if self.dano_ttl > 0:
                # Destello rojo al perder vida (mejoras 2026-10).
                pygame.draw.rect(self.ventana, paleta.PELIGRO,
                                 area.inflate(6, 6), 4)
                self.dano_ttl -= 1
            if self.golpe_ttl > 0:
                self.golpe_ttl -= 1
                if self.golpe_ttl == 0:
                    self.golpe = None
            if self.ataque_ttl > 0:
                self.ataque_ttl -= 1
            if self.trampas_fuego:
                # El chispazo dura 12 frames como el resto del feedback.
                self.trampas_fuego = {i: ttl - 1 for i, ttl in self.trampas_fuego.items()
                                      if ttl > 1}
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
                    dx = dy = 0
                    vistos = set()
                    for tecla, direccion in entrada.MOVER.items():
                        if held[tecla] and direccion not in vistos:
                            vistos.add(direccion)
                            ix, iy = VECTOR_DIRECCION[direccion]
                            dx += ix
                            dy += iy
                    if dx or dy:  # un solo paso por frame, ya normalizado
                        self._mover_libre(dx, dy)
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
