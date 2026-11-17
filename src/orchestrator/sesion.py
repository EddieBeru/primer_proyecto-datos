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
from src.models.errors import NotFoundError
from src.models.conocimiento import preparar_metadatos, MapaDTO
from src.estructuras.tabla_indice import TablaIndice

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
        self._armadas = TablaIndice()
        self._metadatos = preparar_metadatos(loader.plano.values())

    def datos_sala(self, sala_id):
        try:
            return self._metadatos[sala_id]
        except KeyError:
            raise NotFoundError(f"Sala {sala_id} inexistente") from None

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
        self._armadas[n] = True
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
            vecinas = []
            vistas = TablaIndice()
            for salida in room.salidas.values():
                destino = salida.sala
                if (destino != n and destino in self.loader.plano
                        and destino not in self._armadas and destino not in vistas):
                    vistas[destino] = True
                    vecinas.append(destino)
            vecinas = mergesort(vecinas, clave=int)
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
                 almacen_ruta: str | None = None, checkpoint_cada: int = 20) -> None:
        if backend is None:
            from src.controller1 import endpoints as backend
        if type(checkpoint_cada) is not int or checkpoint_cada < 1:
            raise ValueError("K debe ser entero ≥1")
        self.checkpoint_cada = checkpoint_cada
        self.linea = None
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
        self._preparacion_inicio = None
        self._reporte_resolubilidad = None
        self._mem = BitacoraMemoria()
        self._volcadas = 0
        self._archivo: Bitacora | None = Bitacora(log_ruta) if log_ruta else None

    # -- ciclo de vida --
    def preparar_inicio(self, cripta_id: str, contar_lista: bool = True):
        """Obtiene solo datos generales, plano y ubicaciones; no crea partida."""
        from src.algoritmos.resolubilidad import verificar_resolubilidad
        from src.models.resolubilidad import UbicacionesLlaves, ResultadoResolubilidad
        from src.controller1 import endpoints
        from src.controller1.endpoints import esqueleto_completo
        try:
            if self.backend is endpoints:
                info, budget = iniciar_cripta(cripta_id, contar_lista=contar_lista)
            else:
                info = self.backend.info_cripta(cripta_id)
                budget = BudgetAdapter(info.presupuesto_solicitudes)
            if hasattr(self.backend, "esqueleto_completo"):
                plano = self.backend.esqueleto_completo(cripta_id, budget, info=info)
            else:
                plano = esqueleto_completo(cripta_id, budget, info=info)
            proveedor_llaves = getattr(self.backend, "ubicaciones_llaves", None)
            almacen_llaves = None
            if self.cache_ruta is not None:
                from src.controller1.almacen_llaves import AlmacenLlaves
                ruta_llaves = f"{self.cache_ruta}.llaves-{cripta_id.encode('utf-8').hex()}.json"
                almacen_llaves = AlmacenLlaves(ruta_llaves)
                ubicaciones = almacen_llaves.obtener(cripta_id, info.version)
            else:
                ubicaciones = None
            if ubicaciones is None:
                if proveedor_llaves is None:
                    ubicaciones = UbicacionesLlaves(cripta_id, info.version, False, ())
                else:
                    ubicaciones = proveedor_llaves(cripta_id, budget, info.version)
                if almacen_llaves is not None and ubicaciones.completa:
                    almacen_llaves.guardar(ubicaciones)
            resultado = verificar_resolubilidad(info, plano, ubicaciones)
            version, datos, presupuesto = info.version, info, budget
        except (CriptaError, ValueError, TypeError) as exc:
            resultado = ResultadoResolubilidad(
                cripta_id, getattr(locals().get("info"), "version", ""),
                "incompleta", str(exc))
            version, datos, presupuesto, plano = resultado.version_cripta, None, None, None
        self._reporte_resolubilidad = resultado
        self._preparacion_inicio = (cripta_id, version, datos, presupuesto, plano,
                                    resultado, contar_lista)
        return resultado

    def reporte_inicio(self):
        return self._reporte_resolubilidad

    def iniciar(self, cripta_id: str, semilla: int = 0, forzar: bool = False,
                contar_lista: bool = True) -> FotoEstado:
        """Prepara todo y deja la foto inicial (Flujos B + H + §2.4)."""
        from src.controller1 import endpoints as ep
        preparado = self._preparacion_inicio
        if preparado is None or preparado[0] != cripta_id:
            self.preparar_inicio(cripta_id, contar_lista=contar_lista)
            preparado = self._preparacion_inicio
        _, version_preparada, info, budget, plano, resultado, _ = preparado
        from src.models.errors import InicioNoPermitidoError
        if resultado.estado == "incompleta" or (resultado.estado == "no_resoluble" and not forzar):
            raise InicioNoPermitidoError(resultado)
        self.info = info
        self.budget = budget
        # info.version ya es la versión de la cripta: pedir version_cripta
        # aparte cuesta 1 solicitud por 43 bytes idénticos. Se omite.
        ver_cat = self.backend.version_catalogo(budget)
        self.cache = self._abrir_cache(ver_cat.version)
        self.almacen = self._abrir_almacen(ver_cat.version)
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
        self.fachada._sync()
        from src.controller2.linea_tiempo import LineaTiempo
        self.linea = LineaTiempo(self.estado, self.checkpoint_cada)
        self.fachada.receptor_historia = self.linea
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
                from src.controller2.movimiento import sincronizar_puertas_sala
                sincronizar_puertas_sala(self.estado, s)
                self.estado.salas[s.id] = s
            elif self.estado.salas[s.id].contenido_pendiente:
                self.estado.salas[s.id].incorporar_contenido(s)

    def paso(self, texto: str, grabar: bool = True, _automatico: bool = False) -> tuple[bool, str, FotoEstado]:
        """Una intención del jugador + drenaje §2.3. Nunca crashea (error amable)."""
        assert self.fachada is not None, "llamar iniciar() primero"
        partes = texto.strip().split()
        comando = partes[0].lower() if partes else ""
        if comando == "historia":
            try:
                if len(partes) != 2: raise ValueError("Uso: historia <t|#k>")
                consulta = partes[1]
                r = self.historia_accion(int(consulta[1:])) if consulta.startswith('#') else self.historia(int(consulta))
                return True, r.texto(), self.foto()
            except ValueError as exc:
                return False, str(exc), self.foto()
        if comando in ("mapa", "foto", "inventario", "ayuda"):
            return True, "Consulta sin tiempo.", self.foto()
        if comando == "cancelar":
            ok, msg = self.fachada.cancelar_viaje()
            return ok, msg, self.foto()
        if comando == "ir":
            import re
            self.fachada.cancelar_viaje()
            if len(partes) != 3 or partes[1].lower() != "a" or not re.fullmatch(r"[+-]?[0-9]+", partes[2]):
                self.fachada.error = "Uso: ir a <id entero>."
                return False, self.fachada.error, self.foto()
            destino = int(partes[2])
            ok, msg = self.fachada.iniciar_viaje(destino)
            if ok:
                self._mem.anotar(f"#ir-a {destino}")
                if grabar:
                    self._volcar_bitacora()
            return ok, msg, self.foto()
        if not _automatico:
            self.fachada.cancelar_viaje()
        sala_antes = self.fachada.estado.sala_actual
        # Fixtures y consumidores técnicos pueden preparar estado antes de la primera acción.
        if self.linea is not None and not self.linea.acciones:
            from src.controller2.linea_tiempo import LineaTiempo
            self.fachada._sync()
            self.linea = LineaTiempo(self.estado, self.checkpoint_cada)
            self.fachada.receptor_historia = self.linea
        self._mensajes_antes = self.fachada.mensajes.ultimos()
        log_antes = len(self._mem._lineas)
        reloj_antes = self.estado.reloj
        if self.linea is not None: self.linea.comenzar()
        try:
            ok, msg = self._intencion(texto)
        except Exception as exc:
            if self.linea is not None:
                self._restaurar_transaccion_historica(log_antes)
            self.fachada.error = f'No se pudo ejecutar la acción: {exc}'
            return False, self.fachada.error, self.foto()
        if ok and self.linea is not None and len(self.linea.registros) == self.linea._inicio:
            # Un éxito sin cambios (p. ej. puerta ya abierta) no es una acción
            # histórica y tampoco debe consumir el turno pendiente.
            self.linea.descartar()
            return True, msg, self.foto()
        if ok:
            if self.linea is not None:
                self.fachada._sync()
                self.linea.evento()
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
        if self.linea is not None:
            try:
                if ok:
                    self.fachada._sync()
                    if comando == 'deshacer' or (comando == 'usar' and self._mem.leer() and '|deshacer|' in self._mem.leer()[-1]):
                        self.linea.truncar_intervalo({'reloj': reloj_antes})
                    else:
                        self.linea.cerrar_accion({'reloj': reloj_antes}, self.estado)
                else:
                    self.linea.conocimiento()
                    if len(self.linea.registros) > self.linea._inicio:
                        self._restaurar_transaccion_historica(log_antes)
                    else:
                        self.linea.descartar()
            except Exception as exc:
                self._restaurar_transaccion_historica(log_antes)
                ok, msg = False, f'No se pudo registrar la acción: {exc}'
                self.fachada.error = msg
        foto = self.foto()
        if grabar:
            self._volcar_bitacora()
        return ok, msg, foto

    def _restaurar_transaccion_historica(self, log_antes):
        from src.controller2.agenda import Agenda
        from src.controller2.azar import Azar
        from src.controller2.deshacer import PilaDeshacer
        from src.controller2.reloj import RelojVirtual
        from src.controller2.registro_mutaciones import enlazar
        anterior = self.linea.revertir()
        self.estado = EstadoPartida.desde_dict(anterior)
        self.fachada.estado = self.estado
        self.fachada.agenda = Agenda.desde_lista(self.estado.agenda)
        self.fachada.agenda._seq = self.estado.agenda_seq
        self.fachada.pila = PilaDeshacer.desde_lista(self.estado.pila_deshacer)
        self.fachada.reloj = RelojVirtual(self.estado.reloj)
        ae = self.estado.azar_estado
        self.fachada.azar = Azar.desde_estado(self.estado.semilla,self.estado.azar_llamadas,
            (ae[0],tuple(ae[1]),ae[2]))
        self.linea.estado = self.estado
        self.linea._conocimiento = anterior['conocimiento']
        enlazar(self.estado,self.linea)
        del self._mem._lineas[log_antes:]
        self.fachada.mensajes.limpiar()
        for mensaje in self._mensajes_antes: self.fachada.mensajes.agregar(mensaje)

    def avanzar_viaje(self, grabar=True):
        assert self.fachada is not None
        f = self.fachada
        if not f.viaje.activo:
            return True, "Sin viaje activo.", self.foto()
        contexto = f.abrir_contexto_viaje()
        ok, mensaje = True, ""
        try:
            if self.estado.estado != "jugando":
                f.viaje.detener("fin_partida")
            elif any(e.vivo for e in self.estado.sala_en_curso().enemigos):
                f.viaje.detener("enemigos")
            else:
                ruta = f.preparar_paso_viaje()
                if not ruta.alcanzable or ruta.direccion is None:
                    f.viaje.detener("destino" if self.estado.sala_actual == f.viaje.destino else "sin_ruta")
                else:
                    ok, mensaje, _ = self.paso(ruta.direccion, grabar=grabar, _automatico=True)
                    if not ok:
                        contexto.error = mensaje
                        # El rechazo de puerta se observa y no se reintenta aquí.
                        f.preparar_paso_viaje()
        except Exception as exc:
            ok, mensaje = False, str(exc)
            contexto.error = mensaje
            f.error = mensaje
        finally:
            if f.error and contexto.error is None:
                contexto.error = f.error
            f.finalizar_paso_viaje(contexto)
        return ok, mensaje or ("Viaje detenido: " + f.viaje.ultimo_motivo if not f.viaje.activo else ""), self.foto()

    def historia(self, t):
        assert self.linea is not None
        return self.linea.consultar(t=t)

    def historia_accion(self, k):
        assert self.linea is not None
        return self.linea.consultar(accion=k)

    def historial_disponible(self):
        """Metadatos de navegación, sin exponer la estructura histórica."""
        return tuple((i+1,a[1],a[2]) for i,a in enumerate(self.linea.acciones))

    def mapa_conocido(self):
        from src.controller2.conocimiento import _registro
        assert self.estado is not None
        mapa = self.estado.conocimiento
        registros = []
        for sala in mapa.salas():
            registro = _registro(sala)
            if sala.estado == "explorada":
                for salida, dto in zip(sala.salidas, registro["salidas"]):
                    dto["estado"] = mapa.puerta(salida.puerta_id)
            else:
                registro["etiqueta"] = "sala avistada"
            registros.append(registro)
        return MapaDTO(tuple(mergesort(registros, clave=lambda s: s["id"])), mapa.revision)

    def pausar(self):
        assert self.fachada is not None
        self.fachada.pausar()

    def reanudar(self):
        assert self.fachada is not None
        self.fachada.reanudar()

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
        if not self.linea.acciones:
            from src.controller2.linea_tiempo import LineaTiempo
            self.linea = LineaTiempo(self.estado, self.checkpoint_cada)
            self.fachada.receptor_historia = self.linea
        data["historia"] = self.linea.a_dict()
        savegame.guardar(ruta, data)
        try:
            self.cache.guardar_disco(cache_ruta or (ruta + ".cache"))
        except Exception:
            pass
        return data

    def _candidato_carga(self, ruta, en_frio):
        from src.controller1 import savegame
        from copy import copy, deepcopy
        data = savegame.cargar_historia(ruta)
        candidato = Sesion(backend=self.backend, cache_size=self.cache_size, jugador=self.jugador)
        if en_frio:
            # No instalar sesión ni escribir log/caché activos durante preparación.
            candidato.iniciar(data["cripta_id"], semilla=int(data.get("semilla", 0)))
        else:
            assert self.fachada is not None and self.budget is not None
            candidato.info = self.info
            candidato.budget = copy(self.budget)
            candidato.cache = deepcopy(self.cache)
            candidato.almacen = None  # No escribir almacén activo durante validación.
            candidato.loader = RoomLoader(data["cripta_id"], self.loader.plano,
                candidato.budget, candidato.cache, backend=self.backend)
            candidato.proveedor = ProveedorSesion(candidato.loader, registrador=candidato._registrar_vecinas)
            estado_aislado = EstadoPartida.desde_dict(self.estado.a_dict())
            candidato.fachada = Fachada(estado_aislado, candidato.proveedor, candidato.proveedor.catalogo)
        ok_c, ok_k = savegame.validar_versiones(data, candidato.budget, backend=self.backend)
        if not (ok_c and ok_k):
            raise GuardadoError("versión incompatible: no se puede garantizar partida fiel")
        candidato.fachada.cargar(data)
        from src.controller2.linea_tiempo import LineaTiempo
        try:
            candidato.linea = LineaTiempo.desde_dict(data['historia'], candidato.fachada.estado, candidato.proveedor.datos_sala)
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            raise GuardadoError(f"historia inválida: {exc}") from exc
        candidato.fachada.receptor_historia = candidato.linea
        candidato.estado = candidato.fachada.estado
        candidato._recargar_catalogo()
        candidato.fachada.catalogo = candidato.proveedor.catalogo
        if self.estado is not None:
            candidato.estado.conocimiento.revision = self.estado.conocimiento.revision + 1
        restantes = int(data.get("presupuesto_restante", candidato.budget.get_presupuesto()))
        candidato.budget.presupuesto = restantes
        candidato.budget.realizadas = candidato.budget.inicial - restantes
        return candidato

    def _instalar_carga(self, candidato):
        for atributo in ("info", "budget", "cache", "almacen", "loader", "proveedor", "estado", "fachada", "linea"):
            setattr(self, atributo, getattr(candidato, atributo))
        self.proveedor.registrador = self._registrar_vecinas
        self.checkpoint_cada = self.linea.k
        self.fachada.bitacora = self._mem
        self._fijar_fichas_en_uso()
        return self.foto()

    def cargar(self, ruta: str) -> FotoEstado:
        """Instalar solo tras validar formato, conocimiento, versiones y catálogo."""
        return self._instalar_carga(self._candidato_carga(ruta, en_frio=False))

    def cargar_en_frio(self, ruta: str) -> FotoEstado:
        return self._instalar_carga(self._candidato_carga(ruta, en_frio=True))

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
    def reproducir(self, ruta_log: str, hasta: int | None = None) -> FotoEstado:
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
            if "header" in h or "comentario" in h:
                continue
            # Consecuencias y turnos enemigos ya los ejecuta el drenaje.
            if h.get("actor", h.get("quien")) == "jugador":
                self._aplicar_replay(h["tipo"], h["detalle"])
        if hasta is not None:
            return self.historia(min(hasta, self.estado.reloj))
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
