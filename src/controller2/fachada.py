"""Fachada hacia la Vista (K5): unica puerta entre Vista y Controlador. §2/§10 doc oficial."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.controller2.agenda import Agenda
from src.controller2.azar import Azar
from src.controller2.bitacora import BitacoraMemoria, formatear
from src.controller2.combate import ataque_enemigo, ataque_jugador
from src.controller2.deshacer import PilaDeshacer, deshacer_una
from src.controller2.efectos import (
    REGENERACION_PERIODO,
    aplicar_cambio_velocidad,
    ejecutar_fin_efecto,
    ejecutar_quemadura,
    ejecutar_rearme,
    ejecutar_regeneracion,
    ejecutar_veneno,
    pisar_trampa,
    usar_antidoto,
    usar_antorcha,
    usar_pocion,
)
from src.controller2.enemigos import (OLEADA_CADA, activar_sala,
                                        comportamiento_de, ejecutar_oleada,
                                        programar_oleada, turno_enemigo)
from src.controller2.inventario import Inventario, InventarioLlenoError
from src.controller2.modelo import EstadoPartida
from src.controller2.movimiento import abrir_puerta, ejecutar_cierre, intentar_mover
from src.controller2.reloj import COSTOS, RelojVirtual, intervalo
from src.controller2.victoria import actualizar_estado


@dataclass
class FotoEstado:
    """Lo que la Vista dibuja (§10.2: sala, salidas, enemigos, suelo, vida, efectos, 20 msgs)."""
    sala_id: int
    sala_nombre: str
    puertas: dict = field(default_factory=dict)
    objetos_suelo: list = field(default_factory=list)
    trampas: list = field(default_factory=list)
    jugador: dict = field(default_factory=dict)
    enemigos: list = field(default_factory=list)
    inventario: list = field(default_factory=list)
    equipado: str | None = None
    armadura_equipada: str | None = None
    arma_equipada: str | None = None
    pergaminos: int = 0
    mensajes: list = field(default_factory=list)
    presupuesto: int = 0
    estado: str = "jugando"
    error: str | None = None
    en_pausa: bool = False
    sala_oscura: bool = False  # mejoras 2026-10: la vista pone el velo de oscuridad


class Fachada:
    """Ventanilla del Controlador. Dibuja con foto(), juega con intenciones."""

    def __init__(self, estado: EstadoPartida, proveedor, catalogo: dict | None = None,
                 bitacora=None, semilla: int | None = None, orden_fn=None,
                 oleada_cada: int | None = None) -> None:
        self.estado = estado
        self.proveedor = proveedor
        self.catalogo: dict = catalogo or {}
        self.orden_fn = orden_fn  # sorts de C1 inyectados por la Sesión (§4.1/§5.1)
        self.oleada_cada = OLEADA_CADA if oleada_cada is None else int(oleada_cada)
        self.bitacora = bitacora or BitacoraMemoria()
        self.agenda = Agenda.desde_lista(estado.agenda or [])
        self.reloj = RelojVirtual(ahora=estado.reloj)
        self.pila = PilaDeshacer.desde_lista(estado.pila_deshacer or [])
        seed = int(semilla) if semilla is not None else int(getattr(estado, "semilla", 0))
        self.estado.semilla = seed
        self.azar = Azar(seed)
        # Restaura estado RNG si existe (guardado).
        ae = getattr(estado, "azar_estado", None)
        if ae is not None:
            try:
                import random as _rm
                st = ae
                if isinstance(st, list):
                    st = (st[0], tuple(st[1]), st[2] if len(st) < 4 else st[3] if len(st) > 3 else None)
                self.azar._rng.setstate(st)  # type: ignore[arg-type]
                self.azar.llamadas = int(getattr(estado, "azar_llamadas", 0))
            except Exception:
                pass
        self.mensajes: list[str] = []
        self.error: str | None = None
        self.en_pausa = False
        # Activa sala inicial §2.4 (rastro 0 + enemigos activos orden instancia).
        try:
            if estado.sala_actual in estado.salas:
                s0 = estado.salas[estado.sala_actual]
                if s0.ultima_visita is None:
                    s0.ultima_visita = 0
                activar_sala(estado, self.agenda, self.reloj.ahora,
                             estado.sala_actual, self.catalogo)
                self._programar_turno_jugador(COSTOS["mover"], inicial=True)
                self._asegurar_oleada()
        except Exception:
            pass

    def _asegurar_oleada(self) -> None:
        """Una oleada programada siempre (sin duplicar; vive en agenda K2)."""
        try:
            if not any(e.tipo == "oleada" for e in self.agenda):
                programar_oleada(self.agenda, self.reloj, self.oleada_cada)
        except Exception:
            pass

    # -- internos --
    def _sync(self) -> None:
        self.estado.agenda = self.agenda.a_lista()
        self.estado.reloj = self.reloj.ahora
        self.estado.pila_deshacer = self.pila.a_lista()
        try:
            self.estado.azar_llamadas = self.azar.llamadas
            self.estado.azar_estado = self.azar._rng.getstate()
        except Exception:
            pass

    def _anotar(self, tipo: str, actor: str, detalle: str = "") -> None:
        try:
            linea = formatear(self.reloj.ahora, tipo, actor, detalle)
        except ValueError:
            return
        try:
            self.bitacora.anotar(linea)
        except Exception:
            pass
        self.mensajes.append(linea)
        # §4.8: memoria constante, últimos 20 (sin desplazar físicamente: slice).
        if len(self.mensajes) > 20:
            self.mensajes = self.mensajes[-20:]

    def _fail(self, mensaje: str) -> tuple[bool, str]:
        self.error = mensaje
        return False, mensaje

    def _ok(self, mensaje: str = "") -> tuple[bool, str]:
        self.error = None
        if mensaje:
            self.mensajes.append(mensaje)
            if len(self.mensajes) > 20:
                self.mensajes = self.mensajes[-20:]
        self._sync()
        actualizar_estado(self.estado)
        return True, mensaje

    def _cierre_restante(self, sala_id: int, direccion: str) -> int | None:
        """Ticks hasta el cierre automático de la puerta (None si no hay)."""
        restante: int | None = None
        for ev in self.agenda:
            d = ev.datos or {}
            if ev.tipo == "cierre_puerta" and d.get("sala") == sala_id \
                    and d.get("direccion") == direccion:
                r = ev.t - self.reloj.ahora
                if r >= 0 and (restante is None or r < restante):
                    restante = r
        return restante

    def _tipo_de(self, instancia_id: str) -> str | None:
        for sala in self.estado.salas.values():
            for e in sala.enemigos:
                if e.instancia == instancia_id:
                    return e.tipo_id
        return None

    def _tras_accion(self, costo_key: str) -> None:
        """Común tras acción exitosa que consume tiempo: rastro + turno + contador."""
        try:
            self.estado.acciones_jugador = int(getattr(self.estado, "acciones_jugador", 0)) + 1
        except Exception:
            pass
        sala = self.estado.salas.get(self.estado.sala_actual)
        if sala is not None:
            sala.ultima_visita = self.reloj.ahora
        self._programar_turno_jugador(COSTOS[costo_key])

    def _programar_turno_jugador(self, costo: int, inicial: bool = False) -> None:
        try:
            vel = int(self.estado.jugador.velocidad)
        except Exception:
            vel = 100
        self.reloj.programar_turno(self.agenda, "jugador", vel,
                                    {"kind": "jugador", "costo": int(costo)}, costo=int(costo))

    def _disparar_trampas_sala(self) -> None:
        """§2.10: al entrar, trampas armadas se activan antes del siguiente evento."""
        sala = self.estado.salas.get(self.estado.sala_actual)
        if sala is None:
            return
        for t in list(sala.trampas):
            if not t.armada:
                continue
            res, inversa = pisar_trampa(self.estado, self.agenda, self.reloj,
                                        t.instancia, self.catalogo)
            if res.ok:
                if inversa:
                    self.pila.apilar(inversa)
                self._anotar("efecto", "trampa", t.instancia)

    # -- puertas y movimiento §2.5 (abrir costo 50, mover costo 100) --
    def abrir(self, direccion: str) -> tuple[bool, str]:
        res = abrir_puerta(self.estado, direccion, self.agenda, self.reloj)
        if not res.ok:
            # Ya abierta cuenta como éxito sin tiempo (Apéndice B: sin llave rechaza sin tiempo).
            if res.mensaje == "Ya estaba abierta.":
                return self._ok(res.mensaje)
            return self._fail(res.mensaje)
        self.pila.apilar({"op": "abrir", "datos": {"sala": self.estado.sala_actual,
                          "direccion": direccion}, "eventos":
                          [res.evento_cierre_seq] if res.evento_cierre_seq is not None else []})
        self._anotar("abrir", "jugador", direccion)
        self._tras_accion("abrir")
        return self._ok()

    def mover(self, direccion: str) -> tuple[bool, str]:
        origen = self.estado.sala_actual
        res = intentar_mover(self.estado, direccion, self.proveedor, self.agenda,
                             self.reloj, self.catalogo)
        if not res.ok:
            return self._fail(res.mensaje)
        self.pila.apilar({"op": "mover", "datos": {"origen": origen, "abrio": False,
                          "sala_puerta": origen, "direccion": direccion}, "eventos": []})
        self._anotar("mover", "jugador", direccion)
        self._disparar_trampas_sala()
        self._tras_accion("mover")
        return self._ok()

    def esperar(self) -> tuple[bool, str]:
        self._anotar("mover", "jugador", "esperar")
        self._tras_accion("mover")
        return self._ok()

    # -- combate (C2-6 §2.6) --
    def atacar(self, instancia_id: str) -> tuple[bool, str]:
        tipo = self._tipo_de(instancia_id)
        ficha = self.catalogo.get(tipo) if tipo else None
        atk_e = int(getattr(ficha, "ataque", 0) or 0)
        def_e = int(getattr(ficha, "defensa", 0) or 0)
        suelta = list(getattr(ficha, "suelta", None) or [])
        sala = self.estado.salas.get(self.estado.sala_actual)
        objetivo = next((e for e in (sala.enemigos if sala else []) if e.instancia == instancia_id), None)
        vida_antes = objetivo.vida_actual if objetivo else 0
        res = ataque_jugador(self.estado, instancia_id, atk_e, def_e, suelta,
                             self.catalogo, azar=self.azar, agenda=self.agenda)
        if res.dano == 0 and res.mensaje:
            return self._fail(res.mensaje)
        self.pila.apilar({"op": "dano_enemigo", "datos": {"instancia": instancia_id,
                          "vida_antes": vida_antes, "botin": res.botin}, "eventos": []})
        self._anotar("atacar", "jugador", instancia_id)
        if res.mato:
            self._anotar("muerte", instancia_id, "jugador")
        self._tras_accion("atacar")
        return self._ok(f"Daño {res.dano}.")

    def ataque_enemigo(self, instancia_id: str) -> tuple[bool, str]:
        tipo = self._tipo_de(instancia_id)
        ficha = self.catalogo.get(tipo) if tipo else None
        atk = int(getattr(ficha, "ataque", 0) or 0)
        vida_antes = self.estado.jugador.vida_actual
        res = ataque_enemigo(self.estado, instancia_id, atk, self.catalogo, azar=self.azar)
        if res.dano == 0 and res.mensaje:
            return self._fail(res.mensaje)
        self.pila.apilar({"op": "dano_jugador", "datos": {"vida_antes": vida_antes}, "eventos": []})
        self._anotar("dano", instancia_id, str(res.dano))
        return self._ok()

    # -- inventario (C2-5 §2.7; Apéndice B: lleno rechaza sin tiempo) --
    def recoger(self, item_id: str) -> tuple[bool, str]:
        sala = self.estado.salas.get(self.estado.sala_actual)
        if sala is None or item_id not in sala.objetos_suelo:
            return self._fail("No está en el suelo.")
        inv = Inventario.desde_jugador(self.estado.jugador.inventario, self.estado.inventario_max)
        try:
            inv.recoger(item_id)
        except InventarioLlenoError:
            return self._fail(f"Mochila llena ({self.estado.inventario_max}).")
        pos = sala.objetos_suelo.index(item_id)
        sala.objetos_suelo.remove(item_id)
        self.estado.jugador.inventario = inv.a_lista()
        self.pila.apilar({"op": "recoger", "datos": {"item": item_id,
                          "sala": sala.id, "pos_suelo": pos}, "eventos": []})
        self._anotar("recoger", "jugador", item_id)
        self._tras_accion("recoger")
        return self._ok()

    def soltar(self, pos_o_id) -> tuple[bool, str]:
        inv = Inventario.desde_jugador(self.estado.jugador.inventario, self.estado.inventario_max)
        try:
            if isinstance(pos_o_id, int):
                item = inv.soltar_en(pos_o_id)
                pos = pos_o_id
            else:
                pos = self.estado.jugador.inventario.index(pos_o_id)
                item = inv.soltar_id(pos_o_id)
        except (IndexError, KeyError, ValueError):
            return self._fail("Nada en esa posición.")
        sala = self.estado.salas.get(self.estado.sala_actual)
        if sala is None:
            return self._fail("Sala desconocida.")
        sala.objetos_suelo.append(item)
        self.estado.jugador.inventario = inv.a_lista()
        self.pila.apilar({"op": "soltar", "datos": {"item": item,
                          "sala": sala.id, "pos_inv": min(pos, len(self.estado.jugador.inventario))},
                          "eventos": []})
        self._anotar("soltar", "jugador", item)
        self._tras_accion("soltar")
        return self._ok()

    def equipar(self, pos: int) -> tuple[bool, str]:
        orden_antes = list(self.estado.jugador.inventario)
        arma_antes = self.estado.jugador.arma_equipada
        armadura_antes = self.estado.jugador.armadura_equipada
        inv = Inventario.desde_jugador(orden_antes, self.estado.inventario_max)
        try:
            item = inv.equipar(int(pos))
        except (IndexError, ValueError):
            return self._fail("Nada en esa posición.")
        self.estado.jugador.inventario = inv.a_lista()
        ficha = self.catalogo.get(item)
        # Equipo excluyente: solo un objeto a la vez; equipar uno suelta el otro
        # (sigue en la mochila, solo pierde el bonus). Deshacer restaura ambos.
        if getattr(ficha, "clase", "") == "arma":
            self.estado.jugador.arma_equipada = item
            self.estado.jugador.armadura_equipada = None
        elif getattr(ficha, "clase", "") == "armadura":
            self.estado.jugador.armadura_equipada = item
            self.estado.jugador.arma_equipada = None
        self.pila.apilar({"op": "equipar", "datos": {"orden_antes": orden_antes,
                          "arma_antes": arma_antes, "armadura_antes": armadura_antes},
                          "eventos": []})
        self._anotar("equipar", "jugador", item)
        self._tras_accion("equipar")
        return self._ok()

    def vista_ordenada(self, criterio: str = "nombre") -> list:
        """Vista ordenada sin mutar orden real (§4.5). Sorts inyectados por Sesión."""
        if self.orden_fn is None:
            return list(self.estado.jugador.inventario)
        try:
            return self.orden_fn(list(self.estado.jugador.inventario), self.catalogo, criterio)
        except Exception:
            return list(self.estado.jugador.inventario)

    # -- objetos: usar genérico costo 50 §2.3 --
    def usar(self, item_id: str) -> tuple[bool, str]:
        ficha = self.catalogo.get(item_id)
        clase = getattr(ficha, "clase", "") if ficha is not None else ""
        if clase == "pocion" or (ficha is None and "pocion" in item_id):
            return self.usar_pocion(item_id)
        if clase == "antidoto" or (ficha is None and "antidoto" in item_id):
            return self.usar_antidoto(item_id)
        if clase == "antorcha" or (ficha is None and "antorcha" in item_id):
            return self.usar_antorcha(item_id)
        return self._fail("No se puede usar así.")

    # -- efectos (C2-7 §2.10) --
    def _asegurar_cierre_drenaje(self) -> None:
        """Deja un turno del jugador pendiente si no hay ninguno.

        La vista dispara trampas al pasar por encima (caminar es gratis, sin
        `_tras_accion`). El drenaje de la Sesión corta en el turno del
        jugador; sin marcador correría hasta MAX_DRENAJE (los turnos enemigos
        se reprograman solos). Costo 1 = intervalo mínimo legal: el mundo
        avanza un pelín, no se cobra una acción.
        """
        try:
            tiene = any(e.tipo == "turno" and (e.datos or {}).get("kind") == "jugador"
                        for e in self.agenda)
            if not tiene:
                vel = int(self.estado.jugador.velocidad)
                self.reloj.programar_turno(self.agenda, "jugador", vel,
                                           {"kind": "jugador", "costo": 1}, costo=1)
        except Exception:
            pass

    def pisar_trampa(self, instancia_id: str) -> tuple[bool, str]:
        res, inversa = pisar_trampa(self.estado, self.agenda, self.reloj, instancia_id, self.catalogo)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        self._anotar("efecto", "trampa", instancia_id)
        self._asegurar_cierre_drenaje()
        return self._ok(res.mensaje or f"Trampa: {res.dano} de daño.")

    def usar_pocion(self, pocion_id: str) -> tuple[bool, str]:
        v_antes = int(self.estado.jugador.velocidad)
        res, inversa = usar_pocion(self.estado, self.agenda, self.reloj, pocion_id, self.catalogo)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        ficha = self.catalogo.get(pocion_id)
        mod = int(getattr(ficha, "modificador_velocidad", 0) or 0) if ficha else 0
        if mod:
            try:
                aplicar_cambio_velocidad(self.estado, self.agenda, self.reloj,
                                         v_antes, v_antes + mod, "jugador")
            except Exception:
                pass
        self._anotar("efecto", "jugador", f"pocion:{pocion_id}")
        self._tras_accion("usar")
        return self._ok()

    def usar_antidoto(self, antidoto_id: str) -> tuple[bool, str]:
        res, inversa = usar_antidoto(self.estado, self.agenda, antidoto_id)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        self._anotar("efecto", "jugador", f"antidoto:{antidoto_id}")
        self._tras_accion("usar")
        return self._ok(res.mensaje)

    def usar_antorcha(self, antorcha_id: str) -> tuple[bool, str]:
        res, inversa = usar_antorcha(self.estado, self.agenda, self.reloj, antorcha_id, self.catalogo)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        self._anotar("efecto", "jugador", f"antorcha:{antorcha_id}")
        self._tras_accion("usar")
        return self._ok()

    # -- enemigos (C2-8) y reloj (C2-3) --
    def turno_enemigo(self, instancia_id: str) -> tuple[bool, str]:
        origen = next((e.sala_actual for s in self.estado.salas.values()
                       for e in s.enemigos if e.instancia == instancia_id), None)
        msg = turno_enemigo(self.estado, self.agenda, self.reloj, instancia_id,
                             self.catalogo, azar=self.azar)
        destino = next((e.sala_actual for s in self.estado.salas.values()
                        for e in s.enemigos if e.instancia == instancia_id), None)
        if origen is not None and destino is not None and origen != destino:
            self.pila.apilar({"op": "mover_enemigo", "datos": {"instancia": instancia_id,
                              "origen": origen, "destino": destino}, "eventos": []})
        self._anotar("mover", instancia_id, msg)
        self._sync()
        return True, msg

    def avanzar(self) -> str:
        """Ejecuta el proximo evento (cierre, veneno, rearme, fin, turno, regen)."""
        ev = self.reloj.avanzar(self.agenda)
        if ev is None:
            return "agenda vacía"
        d = ev.datos or {}
        if ev.tipo == "oleada":
            inst, turno_seq = ejecutar_oleada(self.estado, self.agenda, self.reloj,
                                              self.catalogo, self.azar, ev.seq)
            if inst is not None:
                self.pila.apilar({"op": "aparece",
                                   "datos": {"instancia": inst,
                                             "sala": self.estado.sala_actual},
                                   "eventos": [turno_seq] if turno_seq is not None else []})
                self._anotar("efecto", "oleada", inst)
            programar_oleada(self.agenda, self.reloj,
                             int(d.get("cada", self.oleada_cada)))
        elif ev.tipo == "cierre_puerta":
            sala = self.estado.salas.get(d.get("sala"))
            antes = sala.salidas[d["direccion"]].cerrada if sala and d.get("direccion") in (sala.salidas if sala else {}) else None
            ejecutar_cierre(self.estado, d.get("sala"), d.get("direccion"))
            self.pila.apilar({"op": "cierre", "datos": {"sala": d.get("sala"),
                             "direccion": d.get("direccion"), "cerrada_antes": antes},
                             "eventos": []})
        elif ev.tipo == "rearme_trampa":
            ejecutar_rearme(self.estado, d.get("instancia"))
            self.pila.apilar({"op": "rearme", "datos": {"instancia": d.get("instancia")},
                             "eventos": []})
        elif ev.tipo == "veneno":
            vida_antes = self.estado.jugador.vida_actual
            ejecutar_veneno(self.estado, int(d.get("dano", 1)))
            self.pila.apilar({"op": "veneno_tick", "datos": {"vida_antes": vida_antes,
                             "dano": int(d.get("dano", 1))}, "eventos": []})
        elif ev.tipo == "quemadura":
            vida_antes = self.estado.jugador.vida_actual
            ejecutar_quemadura(self.estado, int(d.get("dano", 1)))
            self.pila.apilar({"op": "dano_jugador", "datos": {"vida_antes": vida_antes},
                              "eventos": []})
        elif ev.tipo == "fin_efecto":
            nombre = d.get("efecto", "")
            tenia = self.estado.jugador.efectos.get(nombre)
            ejecutar_fin_efecto(self.estado, nombre)
            self.pila.apilar({"op": "fin_efecto", "datos": {"efecto": nombre,
                             "valor_antes": tenia}, "eventos": []})
            if nombre == "veloz":
                try:
                    ficha_v = self.estado.jugador.velocidad
                    aplicar_cambio_velocidad(self.estado, self.agenda, self.reloj,
                                             ficha_v + 4, ficha_v, "jugador")
                except Exception:
                    pass
        elif ev.tipo == "regeneracion":
            inst = d.get("instancia")
            antes = next((e.vida_actual for s in self.estado.salas.values()
                          for e in s.enemigos if e.instancia == inst), None)
            tipo = next((e.tipo_id for s in self.estado.salas.values()
                         for e in s.enemigos if e.instancia == inst), None)
            vmax = None
            if tipo and tipo in self.catalogo:
                vmax = int(getattr(self.catalogo[tipo], "vida_max", 0) or 0) or None
            ejecutar_regeneracion(self.estado, inst, int(d.get("cantidad", 1)), vmax)
            # Reprograma siguiente pulso si sigue vivo; su seq va a la pila
            # para que deshacer corte también la regeneración pendiente.
            vivo = any(e.instancia == inst and e.vivo for s in self.estado.salas.values() for e in s.enemigos)
            seq_pulso = None
            if vivo:
                ev2 = self.agenda.programar(self.reloj.ahora + REGENERACION_PERIODO,
                                            "regeneracion", dict(d))
                seq_pulso = ev2.seq
            self.pila.apilar({"op": "regeneracion", "datos": {"instancia": inst,
                             "vida_antes": antes},
                             "eventos": [seq_pulso] if seq_pulso is not None else []})
        elif ev.tipo == "turno" and (d.get("kind") == "enemigo" or d.get("actor", "").startswith("e")):
            actor = d.get("actor")
            sala_a, obj = None, None
            for s in self.estado.salas.values():
                for e in s.enemigos:
                    if e.instancia == actor:
                        sala_a, obj = s, e
                        break
            if obj is None or not obj.vivo:
                self._sync()
                return ev.tipo
            if sala_a is not None and sala_a.id == self.estado.sala_actual:
                vida_antes = self.estado.jugador.vida_actual
                self.ataque_enemigo(actor)
                # ataque_enemigo ya apiló dano_jugador; quita doble conteo de turno:
                self._sync()
                actualizar_estado(self.estado)
                # Reprograma siguiente turno enemigo.
                from src.controller2.enemigos import velocidad_de
                self.reloj.programar_turno(self.agenda, actor,
                                            velocidad_de(self.catalogo, obj.tipo_id),
                                            {"kind": "enemigo", "tipo": obj.tipo_id}, costo=100)
                return ev.tipo
            self.turno_enemigo(actor)
        self._sync()
        actualizar_estado(self.estado)
        return ev.tipo

    # -- deshacer §2.11 (intervalo: una llamada revierte hasta acción jugador) --
    def deshacer(self) -> tuple[bool, str]:
        ok, msg = deshacer_una(self.estado, self.agenda, self.pila, self.catalogo)
        if not ok:
            return self._fail(msg)
        self._anotar("deshacer", "jugador", "")
        self._asegurar_cierre_drenaje()
        return self._ok("Deshecho.")

    def pausar(self) -> None:
        self.en_pausa = True

    def reanudar(self) -> None:
        self.en_pausa = False

    def guardar(self) -> dict:
        self._sync()
        return self.estado.a_dict()

    def cargar(self, data: dict) -> None:
        self.estado = EstadoPartida.desde_dict(data)
        self.agenda = Agenda.desde_lista(self.estado.agenda or [])
        self.reloj = RelojVirtual(ahora=self.estado.reloj)
        self.pila = PilaDeshacer.desde_lista(self.estado.pila_deshacer or [])
        self.azar = Azar(int(getattr(self.estado, "semilla", 0)))
        ae = getattr(self.estado, "azar_estado", None)
        if ae is not None:
            try:
                self.azar._rng.setstate(ae)  # type: ignore[arg-type]
                self.azar.llamadas = int(getattr(self.estado, "azar_llamadas", 0))
            except Exception:
                pass
        self._asegurar_oleada()

    # -- foto K5 (lo unico que la Vista lee) --
    def foto(self) -> FotoEstado:
        sala = self.estado.salas.get(self.estado.sala_actual)
        puertas = {}
        for k, v in (sala.salidas.items() if sala else {}):
            puertas[k] = {"destino": v.destino, "cerrada": v.cerrada,
                          "llave": v.llave,
                          "cierre_en": self._cierre_restante(sala.id, k)
                          if sala is not None else None}
        pergaminos = sum(1 for i in self.estado.jugador.inventario
                         if getattr(self.catalogo.get(i), "clase", "") == "pergamino_retroceso"
                         or "pergamino" in i)
        enemigos = []
        for e in (sala.enemigos if sala else []):
            enemigos.append({"instancia": e.instancia, "tipo": e.tipo_id,
                             "comportamiento": comportamiento_de(self.catalogo, e.tipo_id),
                             "vida": e.vida_actual, "activa": bool(e.activa)})
        j = self.estado.jugador
        return FotoEstado(
            sala_id=self.estado.sala_actual, sala_nombre=sala.nombre if sala else "?",
            puertas=puertas, objetos_suelo=list(sala.objetos_suelo) if sala else [],
            trampas=[{"instancia": t.instancia, "tipo": t.tipo_id, "armada": t.armada}
                     for t in (sala.trampas if sala else [])],
            jugador={"vida": j.vida_actual, "vida_max": j.vida_max, "ataque": j.ataque,
                     "defensa": j.defensa, "velocidad": j.velocidad, "efectos": dict(j.efectos)},
            enemigos=enemigos, inventario=list(j.inventario),
            equipado=j.inventario[0] if j.inventario else None,
            armadura_equipada=j.armadura_equipada,
            arma_equipada=j.arma_equipada, pergaminos=pergaminos,
            mensajes=self.mensajes[-20:], presupuesto=self.estado.presupuesto_restante,
            estado=self.estado.estado, error=self.error, en_pausa=self.en_pausa,
            sala_oscura=bool(getattr(sala, "oscura", False)))

    # -- consola de pruebas 7.2: solo usa la fachada --
    def consola(self, comandos: list[str]) -> list[str]:
        """Ejecuta comandos de texto y devuelve salidas. Plan B si no hay Pygame."""
        salidas = []
        for cmd in comandos:
            p = cmd.strip().split()
            if not p:
                continue
            c = p[0].lower()
            if c in ("n", "s", "e", "o") and len(p) == 1:
                ok, msg = self.mover(c.upper())
                salidas.append(f"mover {c}: {'ok' if ok else msg}")
            elif c == "abrir" and len(p) == 2:
                ok, msg = self.abrir(p[1].upper())
                salidas.append(f"abrir: {'ok' if ok else msg}")
            elif c == "esperar":
                ok, msg = self.esperar()
                salidas.append(f"esperar: {'ok' if ok else msg}")
            elif c == "pisar" and len(p) == 2:
                ok, msg = self.pisar_trampa(p[1])
                salidas.append(f"pisar: {'ok' if ok else msg}")
            elif c == "atacar" and len(p) == 2:
                ok, msg = self.atacar(p[1])
                salidas.append(f"atacar: {msg or 'ok'}")
            elif c == "recoger" and len(p) == 2:
                ok, msg = self.recoger(p[1])
                salidas.append(f"recoger: {'ok' if ok else msg}")
            elif c == "usar" and len(p) == 2:
                ok, msg = self.usar(p[1])
                salidas.append(f"usar: {'ok' if ok else msg}")
            elif c == "soltar" and len(p) == 2:
                ok, msg = self.soltar(int(p[1]) if p[1].isdigit() else p[1])
                salidas.append(f"soltar: {'ok' if ok else msg}")
            elif c == "equipar" and len(p) == 2:
                ok, msg = self.equipar(int(p[1]))
                salidas.append(f"equipar: {'ok' if ok else msg}")
            elif c == "deshacer":
                ok, msg = self.deshacer()
                salidas.append(f"deshacer: {'ok' if ok else msg}")
            elif c == "avanzar":
                salidas.append(f"evento: {self.avanzar()}")
            elif c == "foto":
                f = self.foto()
                salidas.append(f"sala {f.sala_id} {f.sala_nombre} vida {f.jugador['vida']} inv {f.inventario} estado {f.estado}")
            else:
                salidas.append(f"¿{cmd}?")
        return salidas
