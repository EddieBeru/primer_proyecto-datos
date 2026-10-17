"""C1-7 Cargador de salas "listas para jugar" (Flujo C).

`sala_lista(n)` retorna la sala ya armada (mismo `SalaLista` del falso):
contenido en lote de 10 (N + vecinas del plano), fichas desde la LRU
y solo lo faltante vía `lote_catalogo_auto` (incluye `suelta`).
C2 cambia el import del falso a este cargador sin tocar el motor.
"""

from src.controller1.fake_provider import EnemigoListo, ObjetoListo, SalaLista, TrampaLista
from src.controller1 import endpoints
from src.models.catalog import Enemy, Trap
from src.models.errors import NotFoundError, UnexpectedResponseError


class RoomLoader:
    def __init__(self, cripta_id, plano, budget=None, cache=None, backend=None):
        self.cripta_id = cripta_id
        self.plano = plano
        self.budget = budget
        self.cache = cache
        self.backend = backend or endpoints
        self._contenido = {}
        self._fichas = {}  # solo si no hay caché (con caché, ella es el almacén)

    def sala_lista(self, n):
        room = self.plano.get(n)
        if room is None:
            raise NotFoundError(f"sala inexistente: {n}")
        self._asegurar_contenido(n)
        entry = self._contenido.get(n)
        if entry is None:
            raise UnexpectedResponseError(f"contenido sin sala {n}")
        # Mejoras 2026-10: la oscuridad puede venir declarada en el contenido.
        if getattr(entry, "oscura", False):
            room.oscura = True

        fase1 = (
            [e.tipo for e in entry.enemigos]
            + [t.tipo for t in entry.trampas]
            + list(entry.objetos)
        )
        self._asegurar_fichas(fase1)

        suelta = []
        for e in entry.enemigos:
            ficha = self._ficha(e.tipo)
            if not isinstance(ficha, Enemy):
                raise UnexpectedResponseError(f"tipo {e.tipo} no es enemigo")
            suelta.extend(ficha.suelta or [])
        self._asegurar_fichas(suelta)

        enemigos = [
            EnemigoListo(
                instancia=e.instancia,
                ficha=self._ficha(e.tipo),
                vida_actual=e.vida if e.vida is not None else self._ficha(e.tipo).vida_max,
            )
            for e in entry.enemigos
        ]
        objetos = [ObjetoListo(ficha=self._ficha(oid)) for oid in entry.objetos]
        trampas = []
        for t in entry.trampas:
            ficha = self._ficha(t.tipo)
            if not isinstance(ficha, Trap):
                raise UnexpectedResponseError(f"tipo {t.tipo} no es trampa")
            trampas.append(TrampaLista(instancia=t.instancia, ficha=ficha))
        return SalaLista(room=room, enemigos=enemigos, objetos=objetos, trampas=trampas)

    def asegurar_salas(self, ids):
        """Asegura fichas de varias salas ya conocidas en lotes batidos.

        Mejoras 2026-10 (enemigos por todo el mapa): al entrar a una sala se
        resuelven en el mismo lote las fichas de sus vecinas, para que los
        enemigos que caminan entre salas tengan ficha lista. No pide
        contenido nuevo: ya vino en el lote de 10 de `_asegurar_contenido`.
        """
        presentes = [i for i in ids if i in self._contenido]
        fase = []
        for i in presentes:
            entry = self._contenido[i]
            fase += [e.tipo for e in entry.enemigos]
            fase += [t.tipo for t in entry.trampas]
            fase += list(entry.objetos)
        self._asegurar_fichas(fase)
        suelta = []
        for i in presentes:
            for e in self._contenido[i].enemigos:
                try:
                    ficha = self._ficha(e.tipo)
                except UnexpectedResponseError:
                    continue
                if isinstance(ficha, Enemy):
                    suelta.extend(ficha.suelta or [])
        self._asegurar_fichas(suelta)

    def _asegurar_contenido(self, n):
        if n in self._contenido:
            return
        vecinas = sorted(
            s.sala
            for s in self.plano[n].salidas.values()
            if s.sala in self.plano and s.sala not in self._contenido
        )
        lote = [n] + vecinas[:9]
        resp = self.backend.contenido(self.cripta_id, lote, self.budget)
        for entry in resp.contenido:
            self._contenido[entry.sala] = entry

    def _asegurar_fichas(self, ids):
        unicos = list(dict.fromkeys(ids))
        faltantes = [i for i in unicos if not self._tiene(i)]
        if self.budget is not None:
            try:
                for i in unicos:
                    if i in faltantes:
                        self.budget.miss()
                    else:
                        self.budget.hit()
            except Exception:
                pass
        if not faltantes:
            return
        traidas = self.backend.lote_catalogo_auto(faltantes, self.budget)
        for fid, ficha in traidas.items():
            self._guardar_ficha(fid, ficha)

    def _tiene(self, entidad_id):
        if self.cache is not None:
            return self.cache.obtener(entidad_id) is not None
        return entidad_id in self._fichas

    def _guardar_ficha(self, entidad_id, ficha):
        if self.cache is not None:
            self.cache.guardar(entidad_id, ficha)
        else:
            self._fichas[entidad_id] = ficha

    def _ficha(self, entidad_id):
        if self.cache is not None:
            ficha = self.cache.obtener(entidad_id)
        else:
            ficha = self._fichas.get(entidad_id)
        if ficha is None:
            raise UnexpectedResponseError(f"ficha sin traer: {entidad_id}")
        return ficha
