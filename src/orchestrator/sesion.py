"""Sesión de partida: orquestador C1 ↔ C2 ↔ persistencia (§2.3/§4.11/§5.1).

Por qué existe: la Fachada ejecuta intenciones sueltas pero no drena la
agenda entre decisiones (§2.3), no escribe el header de bitácora (§4.11),
no valida versiones al cargar (Flujo G), no sincroniza presupuesto a K2 y
no registra la tabla final (§2.12). main.py solo hacía demo. La Sesión
coordina todo eso sin decidir reglas (C2) ni tocar HTTP/disco directo (C1).

Protocolo backend (mismo que endpoints/offline): info_cripta,
version_catalogo, esqueleto_completo, contenido,
lote_catalogo_auto. version_cripta existe en el backend pero la Sesión
no la pide: info_cripta ya trae version (ahorra 1 solicitud).
"""

from __future__ import annotations

from src.controller1.almacen_fichas import AlmacenFichas
from src.controller1.budget import BudgetAdapter
from src.controller1.gamelog import Bitacora
from src.controller1.lru_cache import CacheLRU
from src.controller1.mergesort import mergesort
from src.controller1.orden import vista_ordenada
from src.controller1.room_loader import RoomLoader
from src.controller1.unicos import unicos
from src.controller2.bitacora import (
    BitacoraIncompatibleError,
    BitacoraMemoria,
    parsear,
    parsear_header,
)
from src.controller2.fachada import Fachada, FotoEstado
from src.controller2.modelo import EnemigoInstancia, EstadoPartida, SalaViva, TrampaInstancia
from src.controller2.victoria import entrada_desde_estado
from src.models.errors import CriptaError, GuardadoError

MAX_DRENAJE = 500


class ProveedorSesion:
    """Adapta RoomLoader (SalaLista con fichas) a lo que pide C2 (SalaViva).

    Acumula `catalogo` {tipo_id: ficha} con todo lo traído: es lo que la
    Fachada necesita para combate/efectos/IA. Vive aquí (no en C2) para que
    el motor nunca vea fichas sin resolver ni cachés.
    """

    def __init__(self, loader: RoomLoader, registrador=None) -> None:
        self.loader = loader
        self.catalogo: dict = {}
        # Mejoras 2026-10: callback para guardar vecinas dormidas en el estado
        # (enemigos por todo el mapa sin pedir contenido extra).
        self.registrador = registrador
        self._armadas: set[int] = set()

    def sala_lista(self, n: int) -> SalaViva:
        sv = self._armar(n)
        self._precargar_vecinas(n)
        return sv

    def _armar(self, n: int) -> SalaViva:
        # §4.4: el fijado de fichas en uso lo hace la Sesión con el estado
        # real (vivos, suelo, inventario); antes se fijaba todo el catálogo
        # y la LRU no podía desalojar nada.
        sl = self.loader.sala_lista(n)
        for e in sl.enemigos:
            self.catalogo[e.ficha.id] = e.ficha
            for drop in (getattr(e.ficha, "suelta", None) or []):
                f = self.loader._ficha(drop)
                self.catalogo[f.id] = f
        for o in sl.objetos:
            self.catalogo[o.ficha.id] = o.ficha
        for t in sl.trampas:
            self.catalogo[t.ficha.id] = t.ficha
        sv = SalaViva.desde_esqueleto(sl.room)
        sv.enemigos = [EnemigoInstancia(e.instancia, e.ficha.id, e.vida_actual, n)
                       for e in sl.enemigos]
        sv.objetos_suelo = [o.ficha.id for o in sl.objetos]
        sv.trampas = [TrampaInstancia(t.instancia, t.ficha.id, n, t.armada)
                      for t in sl.trampas]
        self._armadas.add(n)
        return sv

    def _precargar_vecinas(self, n: int) -> None:
        """Arma las vecinas del plano y las entrega al registrador.

        Mejoras 2026-10: el contenido de las vecinas suele venir en el mismo
        lote de 10 de `sala_lista`; si a alguna le falta contenido, `_armar`
        pide su lote (misma solicitud que se habría hecho al entrar). Se
        arman como salas *dormidas* (§2.4: incorporar contenido no activa
        enemigos). Si algo falla, la precarga se omite en silencio.
        """
        if self.registrador is None:
            return
        try:
            room = self.loader.plano.get(n)
            if room is None:
                return
            vecinas = mergesort({
                s.sala for s in room.salidas.values()
                if s.sala != n and s.sala in self.loader.plano
                and s.sala not in self._armadas
            }, clave=int)
            if not vecinas:
                return
            self.loader.asegurar_salas(vecinas)
            listas = []
            for v in vecinas:
                try:
                    listas.append(self._armar(v))
                except Exception:
                    continue
            if listas:
                self.registrador(listas)
        except Exception:
            pass

    def precargar_vecinas(self, n: int) -> None:
        """Gancho de la Sesión al entrar a una sala (ver `_precargar_vecinas`)."""
        self._precargar_vecinas(n)


class Sesion:
    """Una partida de punta a punta. Ver docstring del módulo."""

    def __init__(self, backend=None, cache_size: int = 25, jugador: str = "jugador",
                 log_ruta: str | None = None, puntajes_ruta: str = "puntajes.jsonl",
                 cache_ruta: str | None = None,
                 almacen_ruta: str | None = None) -> None:
        if backend is None:
            from src.controller1 import endpoints as backend
        self.backend = backend
        self.cache_size = cache_size
        self.jugador = jugador
        self.log_ruta = log_ruta
        self.puntajes_ruta = puntajes_ruta
        self.cache_ruta = cache_ruta
        self.almacen_ruta = almacen_ruta
        self.budget: BudgetAdapter | None = None
        self.cache: CacheLRU | None = None
        self.almacen: AlmacenFichas | None = None
        self.loader: RoomLoader | None = None
        self.proveedor: ProveedorSesion | None = None
        self.estado: EstadoPartida | None = None
        self.fachada: Fachada | None = None
        self.info = None
        self._mem = BitacoraMemoria()
        self._volcadas = 0
        self._archivo: Bitacora | None = Bitacora(log_ruta) if log_ruta else None

    # -- ciclo de vida --
    def iniciar(self, cripta_id: str, semilla: int = 0) -> FotoEstado:
        """Prepara todo y deja la foto inicial (Flujos B + H + §2.4)."""
        from src.controller1 import endpoints as ep
        if self.backend is ep:
            from src.controller1.session import iniciar_cripta
            info, budget = iniciar_cripta(cripta_id)
        else:
            info = self.backend.info_cripta(cripta_id)
            budget = BudgetAdapter(info.presupuesto_solicitudes)
        self.info = info
        self.budget = budget
        # info.version ya es la versión de la cripta: pedir version_cripta
        # aparte cuesta 1 solicitud por 43 bytes idénticos. Se omite.
        ver_cat = self.backend.version_catalogo(budget)
        self.cache = self._abrir_cache(ver_cat.version)
        self.almacen = self._abrir_almacen(ver_cat.version)
        plano = self.backend.esqueleto_completo(cripta_id, budget, info=info)
        self.loader = RoomLoader(cripta_id, plano, budget, self.cache,
                                 backend=self.backend, almacen=self.almacen)
        self.proveedor = ProveedorSesion(self.loader, registrador=self._registrar_vecinas)
        self.estado = EstadoPartida.nueva_partida(info, ver_cat.version, semilla=int(semilla))
        self.estado.registrar_sala(self.proveedor.sala_lista(info.sala_inicial))
        self._fijar_fichas_en_uso()
        self._guardar_cache()
        self.fachada = Fachada(self.estado, self.proveedor, self.proveedor.catalogo,
                               self._mem, semilla=int(semilla), orden_fn=vista_ordenada)
        self._sync_presupuesto()
        if self._archivo is not None:
            self._archivo.iniciar(cripta_id, info.version, ver_cat.version, int(semilla))
        self._volcar_bitacora()
        return self.foto()

    def _registrar_vecinas(self, salas: list[SalaViva]) -> None:
        """Mejoras 2026-10: guarda vecinas dormidas sin marcarlas visitadas.

        Distinto de `EstadoPartida.registrar_sala`: la vecina está en el
        modelo (para que errantes/rastreadores la puedan cruzar) pero la
        partida aún no la visitó, así que no entra en `salas_visitadas`
        (puntaje §2.12) ni se activan sus enemigos (§2.4).
        """
        if self.estado is None:
            return
        for s in salas:
            if s.id not in self.estado.salas:
                self.estado.salas[s.id] = s

    def paso(self, texto: str, grabar: bool = True) -> tuple[bool, str, FotoEstado]:
        """Una intención del jugador + drenaje §2.3. Nunca crashea (error amable)."""
        assert self.fachada is not None, "llamar iniciar() primero"
        sala_antes = self.fachada.estado.sala_actual
        ok, msg = self._intencion(texto)
        if ok:
            self._drenar()
            self._guardar_cache()
            # Mejoras 2026-10: al cambiar de sala se precargan sus vecinas.
            # Si la sala entró como vecina dormida, `sala_lista` no se llamó
            # para ella y sus propias vecinas aún faltaban.
            sala_ahora = self.fachada.estado.sala_actual
            if sala_ahora != sala_antes:
                self.proveedor.precargar_vecinas(sala_ahora)
            self._fijar_fichas_en_uso()
        else:
            # Guía §6: todo rechazo deja foto.error (incl. comando desconocido).
            self.fachada.error = msg
        foto = self.foto()
        if grabar:
            self._volcar_bitacora()
        return ok, msg, foto

    def foto(self) -> FotoEstado:
        assert self.fachada is not None, "llamar iniciar() primero"
        return self.fachada.foto()

    def inventario_ordenado(self, criterio: str | None = None) -> list:
        """Copia ordenada del inventario para la vista (§4.5), sin mutar nada.

        Delega en la fachada, que usa los sorts de C1 inyectados (mergesort/
        inserción); la vista jamás ordena. `criterio` None = orden real.
        """
        assert self.fachada is not None, "llamar iniciar() primero"
        if not criterio:
            return list(self.fachada.estado.jugador.inventario)
        return self.fachada.vista_ordenada(str(criterio))

    def _abrir_cache(self, version_cat: str) -> CacheLRU:
        """Reusa fichas de partidas anteriores si la versión sigue válida."""
        if self.cache_ruta:
            try:
                import os
                if os.path.isfile(self.cache_ruta):
                    cache = CacheLRU.cargar_disco(self.cache_ruta, self.cache_size)
                    cache.invalida_si_cambia(version_cat)
                    return cache
            except Exception:
                pass
        cache = CacheLRU(self.cache_size)
        cache.invalida_si_cambia(version_cat)
        return cache

    def _abrir_almacen(self, version_cat: str) -> AlmacenFichas | None:
        """Almacén persistente de fichas (§4.4): sobrevive al tope de la LRU.

        Sin ruta (tests/offline) no hay almacén: no inventamos caché de
        disco en modos que no la piden. Cripta/catálogo nuevos invalidan.
        """
        ruta = self.almacen_ruta
        if ruta is None and self.cache_ruta:
            ruta = self.cache_ruta + ".fichas"
        if not ruta:
            return None
        almacen = None
        try:
            import os
            if os.path.isfile(ruta):
                almacen = AlmacenFichas.cargar_disco(ruta)
        except Exception:
            almacen = None
        if almacen is None:
            almacen = AlmacenFichas(ruta=ruta)
        almacen.invalida_si_cambia(version_cat)
        return almacen

    def _fijar_fichas_en_uso(self) -> None:
        """Re-fija en la LRU solo lo que la partida usa de verdad (§4.4).

        Incluye enemigos/trampas/suelo de la sala actual (la única cuyas
        fichas se están mostrando) y todo el inventario. El resto queda
        desalojable; si se desaloja, se recupera del almacén sin red.
        """
        if self.cache is None or self.estado is None:
            return
        ids: list[str] = []
        sala = self.estado.salas.get(self.estado.sala_actual)
        if sala is not None:
            ids += [e.tipo_id for e in sala.enemigos]
            ids += [t.tipo_id for t in sala.trampas]
            ids += list(sala.objetos_suelo)
        jugador = self.estado.jugador
        ids += list(jugador.inventario)
        if jugador.arma_equipada:
            ids.append(jugador.arma_equipada)
        if jugador.armadura_equipada:
            ids.append(jugador.armadura_equipada)
        catalogo = self.proveedor.catalogo if self.proveedor else {}
        try:
            self.cache.fijar_en_uso([i for i in unicos(ids) if i in catalogo])
        except Exception:
            pass

    def _guardar_cache(self) -> None:
        if not self.cache_ruta or self.cache is None:
            return
        try:
            self.cache.guardar_disco(self.cache_ruta)
        except Exception:
            pass

    # -- intención + drenaje --
    def _intencion(self, texto: str) -> tuple[bool, str]:
        f = self.fachada
        assert f is not None
        p = texto.strip().split()
        if not p:
            return False, "¿?"
        c = p[0].lower()
        if c in ("n", "s", "e", "o") and len(p) == 1:
            return f.mover(c.upper())
        if c == "abrir" and len(p) == 2:
            return f.abrir(p[1].upper())
        if c == "esperar":
            return f.esperar()
        if c == "pisar" and len(p) == 2:
            # Mejoras 2026-10: la vista dispara la trampa al pasar por encima.
            return f.pisar_trampa(p[1])
        if c == "atacar" and len(p) == 2:
            return f.atacar(p[1])
        if c == "recoger" and len(p) == 2:
            return f.recoger(p[1])
        if c == "usar" and len(p) == 2:
            return f.usar(p[1])
        if c == "soltar" and len(p) == 2:
            return f.soltar(int(p[1]) if p[1].isdigit() else p[1])
        if c == "equipar" and len(p) == 2:
            if p[1].isdigit():
                return f.equipar(int(p[1]))
            try:
                pos = f.estado.jugador.inventario.index(p[1])
            except ValueError:
                return False, "No lo tienes."
            return f.equipar(pos)
        if c == "deshacer":
            return f.deshacer()
        return False, f"¿{texto.strip()}? (ayuda: n/s/e/o, abrir, atacar, esperar, pisar, recoger, usar, soltar, equipar, deshacer)"

    def _drenar(self) -> None:
        """§2.3: ejecuta eventos pendientes hasta el próximo turno del jugador o fin."""
        assert self.fachada is not None and self.estado is not None
        for _ in range(MAX_DRENAJE):
            if self.estado.estado != "jugando":
                break
            try:
                prox = self.fachada.agenda.ver_proximo()
            except AttributeError:
                break
            if prox is None:
                break
            if prox.tipo == "turno" and (prox.datos or {}).get("kind") == "jugador":
                # El marcador se consume al llegar (avanza el reloj y sincroniza).
                # Sin esto tapona la agenda y los turnos enemigos lentos jamás
                # llegan (§2.3: drenar HASTA el turno del jugador, no ANTES).
                try:
                    self.fachada.avanzar()
                except Exception as e:  # §3.1: reportar con contexto, no caer
                    self.fachada.error = f"evento falló: {e}"
                    break
                break
            try:
                self.fachada.avanzar()
            except Exception as e:  # §3.1: reportar con contexto, no caer
                self.fachada.error = f"evento falló: {e}"
                break
        self._sync_presupuesto()

    def _sync_presupuesto(self) -> None:
        if self.budget is not None and self.estado is not None:
            try:
                self.estado.presupuesto_restante = self.budget.get_presupuesto()
            except Exception:
                pass

    def _volcar_bitacora(self) -> None:
        if self._archivo is None:
            return
        lineas = self._mem.leer()
        for ln in lineas[self._volcadas:]:
            try:
                self._archivo.anotar(ln)
            except CriptaError:
                break
        self._volcadas = len(lineas)

    # -- pausa --
    def guardar(self, ruta: str, cache_ruta: str | None = None):
        """Foto completa a binario v2 + caché a disco. Devuelve el dict guardado."""
        from src.controller1 import savegame
        assert self.fachada is not None and self.cache is not None
        self._sync_presupuesto()
        data = self.fachada.guardar()
        savegame.guardar(ruta, data)
        try:
            self.cache.guardar_disco(cache_ruta or (ruta + ".cache"))
        except Exception:
            pass
        return data

    def cargar(self, ruta: str) -> FotoEstado:
        """Carga y valida versiones (Flujo G: mismatch = error, no silencioso)."""
        from src.controller1 import savegame
        assert self.fachada is not None and self.budget is not None
        data = savegame.cargar(ruta)
        if "jugador" not in data:
            raise GuardadoError("formato legado v1 sin estado completo; inicie de nuevo")
        ok_c, ok_k = savegame.validar_versiones(data, self.budget, backend=self.backend)
        if not (ok_c and ok_k):
            raise GuardadoError(
                f"versión incompatible (cripta_ok={ok_c}, catalogo_ok={ok_k}): "
                "no se puede garantizar partida fiel")
        self.fachada.cargar(data)
        self.estado = self.fachada.estado
        self._recargar_catalogo()
        self._fijar_fichas_en_uso()
        restantes = int(data.get("presupuesto_restante", self.budget.get_presupuesto()))
        try:
            self.budget.presupuesto = restantes
            self.budget.realizadas = self.budget.inicial - restantes
        except Exception:
            pass
        return self.foto()

    def cargar_en_frio(self, ruta: str) -> FotoEstado:
        """Resume sin sesión previa: lee el save, inicia su cripta y carga."""
        from src.controller1 import savegame
        data = savegame.cargar(ruta)
        if "jugador" not in data:
            raise GuardadoError("formato legado v1 sin estado completo; inicie de nuevo")
        semilla = int(data.get("semilla", 0))
        self.iniciar(data["cripta_id"], semilla=semilla)
        return self.cargar(ruta)

    def _recargar_catalogo(self) -> None:
        """Tras cargar en otro proceso, trae fichas de tipos referenciados."""
        assert self.estado is not None and self.proveedor is not None
        ids: list[str] = []
        for s in self.estado.salas.values():
            ids += [e.tipo_id for e in s.enemigos]
            ids += [t.tipo_id for t in s.trampas]
            ids += list(s.objetos_suelo)
        ids += list(self.estado.jugador.inventario)
        ids = [i for i in unicos(ids) if i not in self.proveedor.catalogo]
        if not ids:
            return
        faltan = []
        for fid in ids:
            ficha = None
            try:
                if self.cache is not None:
                    ficha = self.cache.obtener(fid)
            except Exception:
                ficha = None
            if ficha is None and self.almacen is not None:
                try:
                    ficha = self.almacen.obtener(fid)
                except Exception:
                    ficha = None
                if ficha is not None and self.cache is not None:
                    try:
                        self.cache.guardar(fid, ficha)
                    except Exception:
                        pass
            if ficha is not None:
                self.proveedor.catalogo[fid] = ficha
            else:
                faltan.append(fid)
        if faltan:
            traidas = self.backend.lote_catalogo_auto(faltan, self.budget)
            for fid, ficha in traidas.items():
                self.proveedor.catalogo[fid] = ficha
                try:
                    if self.cache is not None:
                        self.cache.guardar(fid, ficha)
                except Exception:
                    pass
                try:
                    if self.almacen is not None:
                        self.almacen.guardar(fid, ficha)
                except Exception:
                    pass
        self._guardar_cache()

    # -- replay --
    def reproducir(self, ruta_log: str) -> FotoEstado:
        """--replay sin interacción: valida header y re-ejecuta vía paso()."""
        if self._archivo is None:
            self._archivo = None
        lineas = Bitacora(ruta_log).leer()
        if not lineas or not lineas[0].startswith("#cripta"):
            raise BitacoraIncompatibleError("replay sin header #cripta: no validable")
        head = parsear_header(lineas[0])
        ver_c = self.backend.version_cripta(head["cripta_id"])
        ver_k = self.backend.version_catalogo()
        if ver_c.version != head["version_cripta"] or ver_k.version != head["version_catalogo"]:
            raise BitacoraIncompatibleError(
                f"replay {head['cripta_id']} {head['version_cripta']}/{head['version_catalogo']} "
                f"!= disponible {ver_c.version}/{ver_k.version}: no se garantiza fidelidad")
        self.iniciar(head["cripta_id"], semilla=head["semilla"])
        for ln in lineas[1:]:
            if not ln.strip():
                continue
            h = parsear(ln)
            if "header" in h:
                continue
            self._aplicar_replay(h["tipo"], h["detalle"])
        return self.foto()

    def _aplicar_replay(self, tipo: str, detalle: str) -> None:
        assert self.fachada is not None
        if tipo == "mover":
            self.paso(detalle if detalle != "esperar" else "esperar", grabar=False)
        elif tipo == "abrir":
            self.paso(f"abrir {detalle}", grabar=False)
        elif tipo == "atacar":
            self.paso(f"atacar {detalle}", grabar=False)
        elif tipo == "recoger":
            self.paso(f"recoger {detalle}", grabar=False)
        elif tipo == "soltar":
            self.paso(f"soltar {detalle}", grabar=False)
        elif tipo == "equipar":
            self.paso(f"equipar {detalle}", grabar=False)
        elif tipo == "esperar":
            self.paso("esperar", grabar=False)
        elif tipo in ("efecto", "usar"):
            if detalle.startswith("pocion:") or detalle.startswith("antidoto:") \
                    or detalle.startswith("antorcha:"):
                self.paso(f"usar {detalle.split(':', 1)[1]}", grabar=False)
            elif detalle:
                # Trampa: el mover original ya la disparó (auto); solo reintenta
                # si sigue armada, si no es no-op y se salta (evita doble daño).
                sala = self.estado.salas.get(self.estado.sala_actual) if self.estado else None
                trampas = {t.instancia: t for t in (sala.trampas if sala else [])}
                if detalle in trampas and trampas[detalle].armada:
                    self.fachada.pisar_trampa(detalle)
                    self._drenar()
        elif tipo == "deshacer":
            self.paso("deshacer", grabar=False)
        # dano/muerte/victoria/derrota son consecuencias: se derivan solas.

    # -- fin --
    def finalizar(self) -> dict:
        """Tabla local + reporte red (§2.12/§5.1). Solo al terminar."""
        assert self.estado is not None and self.budget is not None
        if self.estado.estado == "jugando":
            return {"terminada": False, "estado": "jugando"}
        from src.controller1 import puntajes
        entrada = entrada_desde_estado(self.estado, self.jugador)
        try:
            puntajes.registrar(self.puntajes_ruta, {
                "nombre": entrada.nombre, "cripta_id": entrada.cripta_id,
                "version_cripta": entrada.version_cripta, "acciones": entrada.acciones,
                "enemigos_derrotados": entrada.enemigos_derrotados,
                "reloj_final": entrada.reloj_final})
        except Exception as e:
            return {"terminada": True, "estado": self.estado.estado,
                    "puntaje_error": str(e), "red": self.budget.reporte()}
        return {"terminada": True, "estado": self.estado.estado,
                "puntajes_ruta": self.puntajes_ruta, "red": self.budget.reporte()}
