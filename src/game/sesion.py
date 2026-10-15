"""Sesión de partida: orquestador C1 ↔ C2 ↔ persistencia (§2.3/§4.11/§5.1).

Por qué existe: la Fachada ejecuta intenciones sueltas pero no drena la
agenda entre decisiones (§2.3), no escribe el header de bitácora (§4.11),
no valida versiones al cargar (Flujo G), no sincroniza presupuesto a K2 y
no registra la tabla final (§2.12). main.py solo hacía demo. La Sesión
coordina todo eso sin decidir reglas (C2) ni tocar HTTP/disco directo (C1).

Protocolo backend (mismo que endpoints/offline): info_cripta,
version_cripta, version_catalogo, esqueleto_completo, contenido,
lote_catalogo_auto. Ninguno es opcional.
"""

from __future__ import annotations

from src.adapters.budget import BudgetAdapter
from src.adapters.gamelog import Bitacora
from src.adapters.lru_cache import CacheLRU
from src.adapters.room_loader import RoomLoader
from src.controller.bitacora import (
    BitacoraIncompatibleError,
    BitacoraMemoria,
    parsear,
    parsear_header,
)
from src.controller.fachada import Fachada, FotoEstado
from src.controller.modelo import EnemigoInstancia, EstadoPartida, SalaViva, TrampaInstancia
from src.controller.victoria import entrada_desde_estado
from src.models.errors import CriptaError, GuardadoError

MAX_DRENAJE = 500


class ProveedorSesion:
    """Adapta RoomLoader (SalaLista con fichas) a lo que pide C2 (SalaViva).

    Acumula `catalogo` {tipo_id: ficha} con todo lo traído: es lo que la
    Fachada necesita para combate/efectos/IA. Vive aquí (no en C2) para que
    el motor nunca vea fichas sin resolver ni cachés.
    """

    def __init__(self, loader: RoomLoader) -> None:
        self.loader = loader
        self.catalogo: dict = {}

    def sala_lista(self, n: int) -> SalaViva:
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
        return sv


class Sesion:
    """Una partida de punta a punta. Ver docstring del módulo."""

    def __init__(self, backend=None, cache_size: int = 25, jugador: str = "jugador",
                 log_ruta: str | None = None, puntajes_ruta: str = "puntajes.jsonl") -> None:
        if backend is None:
            from src.api import endpoints as backend
        self.backend = backend
        self.cache_size = cache_size
        self.jugador = jugador
        self.log_ruta = log_ruta
        self.puntajes_ruta = puntajes_ruta
        self.budget: BudgetAdapter | None = None
        self.cache: CacheLRU | None = None
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
        from src.api import endpoints as ep
        if self.backend is ep:
            from src.adapters.session import iniciar_cripta
            info, budget = iniciar_cripta(cripta_id)
        else:
            info = self.backend.info_cripta(cripta_id)
            budget = BudgetAdapter(info.presupuesto_solicitudes)
        self.info = info
        self.budget = budget
        ver_cripta = self.backend.version_cripta(cripta_id, budget)
        ver_cat = self.backend.version_catalogo(budget)
        self.cache = CacheLRU(self.cache_size)
        self.cache.invalida_si_cambia(ver_cat.version)
        plano = self.backend.esqueleto_completo(cripta_id, budget, info=info)
        self.loader = RoomLoader(cripta_id, plano, budget, self.cache, backend=self.backend)
        self.proveedor = ProveedorSesion(self.loader)
        self.estado = EstadoPartida.nueva_partida(info, ver_cat.version, semilla=int(semilla))
        self.estado.registrar_sala(self.proveedor.sala_lista(info.sala_inicial))
        self.fachada = Fachada(self.estado, self.proveedor, self.proveedor.catalogo,
                               self._mem, semilla=int(semilla))
        self._sync_presupuesto()
        if self._archivo is not None:
            self._archivo.iniciar(cripta_id, info.version, ver_cat.version, int(semilla))
        self._volcar_bitacora()
        return self.foto()

    def paso(self, texto: str, grabar: bool = True) -> tuple[bool, str, FotoEstado]:
        """Una intención del jugador + drenaje §2.3. Nunca crashea (error amable)."""
        assert self.fachada is not None, "llamar iniciar() primero"
        ok, msg = self._intencion(texto)
        if ok:
            self._drenar()
        foto = self.foto()
        if grabar:
            self._volcar_bitacora()
        return ok, msg, foto

    def foto(self) -> FotoEstado:
        assert self.fachada is not None, "llamar iniciar() primero"
        return self.fachada.foto()

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
        return False, f"¿{texto.strip()}? (ayuda: n/s/e/o, abrir, atacar, esperar, recoger, usar, soltar, equipar, deshacer)"

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
        from src.adapters import savegame
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
        from src.adapters import savegame
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
        restantes = int(data.get("presupuesto_restante", self.budget.get_presupuesto()))
        try:
            self.budget.presupuesto = restantes
            self.budget.realizadas = self.budget.inicial - restantes
        except Exception:
            pass
        return self.foto()

    def cargar_en_frio(self, ruta: str) -> FotoEstado:
        """Resume sin sesión previa: lee el save, inicia su cripta y carga."""
        from src.adapters import savegame
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
        ids = [i for i in dict.fromkeys(ids) if i not in self.proveedor.catalogo]
        if not ids:
            return
        traidas = self.backend.lote_catalogo_auto(ids, self.budget)
        for fid, ficha in traidas.items():
            self.proveedor.catalogo[fid] = ficha
            try:
                if self.cache is not None:
                    self.cache.guardar(fid, ficha)
            except Exception:
                pass

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
        from src.adapters import puntajes
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
