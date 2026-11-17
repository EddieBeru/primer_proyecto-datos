"""Observación de escrituras del modelo; conserva cambios, nunca snapshots por acción."""
from dataclasses import fields, is_dataclass


def dato(valor):
    tipo = type(valor)
    if tipo is int or tipo is str or tipo is bool or tipo is float or valor is None:
        return valor
    if is_dataclass(valor):
        return {f.name: dato(getattr(valor, f.name)) for f in fields(valor)
                if f.name != "contenido_pendiente" or getattr(valor, f.name)}
    if isinstance(valor, dict):
        return {str(k): dato(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [dato(v) for v in valor]
    return valor


def diferencias(antes, despues, ruta=()):
    if antes == despues:
        return
    if type(antes) is dict and type(despues) is dict:
        for k in antes:
            if k not in despues:
                yield [list(ruta + (k,)), True, antes[k], False, None]
        for k in despues:
            if k not in antes:
                yield [list(ruta + (k,)), False, None, True, despues[k]]
            else:
                yield from diferencias(antes[k], despues[k], ruta + (k,))
    elif type(antes) is list and type(despues) is list and len(antes) == len(despues):
        for i, (a, b) in enumerate(zip(antes, despues)):
            yield from diferencias(a, b, ruta + (i,))
    elif type(antes) is list and type(despues) is list:
        inicio = 0
        while inicio < min(len(antes), len(despues)) and antes[inicio] == despues[inicio]: inicio += 1
        fin = 0
        while fin < min(len(antes), len(despues)) - inicio and antes[-fin-1] == despues[-fin-1]: fin += 1
        yield [list(ruta), True, antes[inicio:len(antes)-fin], True, despues[inicio:len(despues)-fin], inicio]
    else:
        yield [list(ruta), True, antes, True, despues]


class Observable:
    def __setattr__(self, nombre, valor):
        receptor = self.__dict__.get('_registro')
        ruta = self.__dict__.get('_ruta', ()) + (nombre,)
        if receptor is not None and nombre in self.__dataclass_fields__:
            if nombre in self.__dict__:
                receptor.cambio(ruta, dato(self.__dict__[nombre]), dato(valor))
            if nombre in self.__dict__:
                desenlazar(self.__dict__[nombre])
            valor = enlazar(valor, receptor, ruta)
        object.__setattr__(self, nombre, valor)


class ListaObservable(list):
    def _cambiar(self, funcion, *args, **kwargs):
        # Preparar el cambio antes de publicarlo: si el registro falla, la lista
        # viva conserva su contenido y sus referencias.
        antes = dato(self)
        previos = list(self)
        candidato = list(self)
        resultado = getattr(candidato, funcion.__name__)(*args, **kwargs)
        self._registro.cambio(self._ruta, antes, dato(candidato))
        list.__setitem__(self, slice(None), candidato)
        for valor in previos:
            if not any(valor is actual for actual in self):
                desenlazar(valor)
        for i, valor in enumerate(self):
            list.__setitem__(self, i, enlazar(valor, self._registro, self._ruta + (i,)))
        return resultado

    def append(self, v): return self._cambiar(super().append, v)
    def extend(self, v): return self._cambiar(super().extend, v)
    def insert(self, i, v): return self._cambiar(super().insert, i, v)
    def remove(self, v): return self._cambiar(super().remove, v)
    def pop(self, i=-1): return self._cambiar(super().pop, i)
    def clear(self): return self._cambiar(super().clear)
    def __setitem__(self, i, v): return self._cambiar(super().__setitem__, i, v)
    def __delitem__(self, i): return self._cambiar(super().__delitem__, i)
    def __iadd__(self, v): self.extend(v); return self


class DiccionarioObservable(dict):
    def __setitem__(self, k, v):
        ruta = self._ruta + (str(k),)
        if k in self:
            self._registro.cambio(ruta, dato(self[k]), dato(v))
        else:
            self._registro.presencia(ruta, False, None, True, dato(v))
        if k in self: desenlazar(self[k])
        super().__setitem__(k, enlazar(v, self._registro, ruta))

    def __delitem__(self, k):
        self._registro.presencia(self._ruta + (str(k),), True, dato(self[k]), False, None)
        desenlazar(self[k])
        super().__delitem__(k)

    def pop(self, k, *default):
        if k not in self:
            if default: return default[0]
            raise KeyError(k)
        v = self[k]; del self[k]; return v

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items(): self[k] = v

    def setdefault(self, k, default=None):
        if k not in self: self[k] = default
        return self[k]

    def clear(self):
        for k in list(self): del self[k]


def enlazar(valor, registro, ruta=()):
    if isinstance(valor, Observable):
        object.__setattr__(valor, '_registro', registro)
        object.__setattr__(valor, '_ruta', ruta)
        for f in fields(valor):
            if f.name != 'conocimiento':
                object.__setattr__(valor, f.name, enlazar(getattr(valor, f.name), registro, ruta + (f.name,)))
    elif isinstance(valor, list):
        nuevo = ListaObservable()
        nuevo._registro, nuevo._ruta = registro, ruta
        for i, v in enumerate(valor): list.append(nuevo, enlazar(v, registro, ruta + (i,)))
        return nuevo
    elif isinstance(valor, dict):
        nuevo = DiccionarioObservable()
        nuevo._registro, nuevo._ruta = registro, ruta
        for k, v in valor.items(): dict.__setitem__(nuevo, k, enlazar(v, registro, ruta + (str(k),)))
        return nuevo
    return valor


def limpio(valor):
    """Serialización del modelo conserva tipos del contrato técnico anterior."""
    tipo = type(valor)
    if tipo is int or tipo is str or tipo is bool or tipo is float or valor is None:
        return valor
    if is_dataclass(valor):
        return {f.name: limpio(getattr(valor,f.name)) for f in fields(valor)
                if f.name != "contenido_pendiente" or getattr(valor, f.name)}
    if isinstance(valor,dict): return {k:limpio(v) for k,v in valor.items()}
    if isinstance(valor,list): return [limpio(v) for v in valor]
    if isinstance(valor,tuple): return tuple(limpio(v) for v in valor)
    return valor


def desenlazar(valor):
    if isinstance(valor, Observable):
        object.__setattr__(valor, '_registro', None)
        for f in fields(valor): desenlazar(getattr(valor,f.name))
    elif isinstance(valor,dict):
        for v in valor.values(): desenlazar(v)
    elif isinstance(valor,list):
        for v in valor: desenlazar(v)


def sincronizar_secuencia(estado, nombre, nueva, ordenada=False):
    """Publicar snapshots de agenda/pila mediante segmentos, sin copiar su prefijo.

    Estas dos listas son proyecciones de las estructuras del motor y solo se
    reemplazan desde Fachada._sync. Los elementos conservados ya están separados
    de esas estructuras; los nuevos se convierten antes de publicar el cambio.
    """
    anterior = getattr(estado, nombre)
    if anterior == nueva:
        return
    cambios = []
    resultado = []
    if ordenada:
        i = j = 0
        while i < len(anterior) or j < len(nueva):
            if i < len(anterior) and j < len(nueva) and anterior[i] == nueva[j]:
                resultado.append(anterior[i]); i += 1; j += 1
                continue
            posicion = len(resultado)
            if j == len(nueva) or (i < len(anterior) and
                    (anterior[i]['t'], anterior[i]['seq']) < (nueva[j]['t'], nueva[j]['seq'])):
                cambios.append([[nombre], True, [dato(anterior[i])], True, [], posicion])
                i += 1
            elif i == len(anterior) or (nueva[j]['t'], nueva[j]['seq']) < (anterior[i]['t'], anterior[i]['seq']):
                valor = dato(nueva[j])
                cambios.append([[nombre], True, [], True, [valor], posicion])
                resultado.append(valor); j += 1
            else:
                valor = dato(nueva[j])
                cambios.append([[nombre], True, [dato(anterior[i])], True, [valor], posicion])
                resultado.append(valor); i += 1; j += 1
    else:
        inicio = 0
        while inicio < min(len(anterior), len(nueva)) and anterior[inicio] == nueva[inicio]:
            inicio += 1
        fin = 0
        while fin < min(len(anterior), len(nueva)) - inicio and anterior[-fin-1] == nueva[-fin-1]:
            fin += 1
        nuevos = [dato(v) for v in nueva[inicio:len(nueva)-fin]]
        cambios.append([[nombre], True, dato(anterior[inicio:len(anterior)-fin]), True, nuevos, inicio])
        resultado = list(anterior[:inicio]) + nuevos + (list(anterior[len(anterior)-fin:]) if fin else [])
    cambios = [c for c in cambios if c[2] != c[4]]
    if not cambios:
        return
    receptor = estado.__dict__.get('_registro')
    if receptor is not None and receptor.activo:
        comienzo = len(receptor.registros)
        try:
            for cambio in cambios:
                receptor.registrar_cambio(receptor.contexto(), cambio)
        except Exception:
            del receptor.registros[comienzo:]
            raise
    object.__setattr__(estado, nombre, resultado)


def copiar_registro(valor):
    """Copiar únicamente el dominio JSON del diario, sin objetos del motor."""
    tipo = type(valor)
    if tipo is list:
        return [copiar_registro(v) for v in valor]
    if tipo is dict:
        return {k: copiar_registro(v) for k, v in valor.items()}
    if tipo is tuple:
        return tuple(copiar_registro(v) for v in valor)
    return valor


def sincronizar_agenda(estado, agenda):
    """Aplicar el diario estructural de agenda mediante búsqueda binaria propia."""
    if agenda._cambios is None:
        sincronizar_secuencia(estado, "agenda", agenda.a_lista(), ordenada=True)
        agenda._cambios = []
        return
    if not agenda._cambios:
        return
    resultado = list(estado.agenda)
    cambios = []
    for insertar, evento in agenda._cambios:
        clave = (evento['t'], evento['seq'])
        izquierda, derecha = 0, len(resultado)
        while izquierda < derecha:
            medio = (izquierda + derecha)//2
            candidato = resultado[medio]
            if (candidato['t'], candidato['seq']) < clave:
                izquierda = medio + 1
            else:
                derecha = medio
        if insertar:
            valor = dato(evento)
            cambios.append([['agenda'], True, [], True, [valor], izquierda])
            resultado.insert(izquierda, valor)
        else:
            if izquierda >= len(resultado) or (resultado[izquierda]['t'], resultado[izquierda]['seq']) != clave:
                raise ValueError('proyección de agenda desincronizada')
            previo = resultado.pop(izquierda)
            cambios.append([['agenda'], True, [dato(previo)], True, [], izquierda])
    receptor = estado.__dict__.get('_registro')
    if receptor is not None and receptor.activo:
        inicio = len(receptor.registros)
        try:
            for cambio in cambios:
                receptor.registrar_cambio(receptor.contexto(), cambio)
        except Exception:
            del receptor.registros[inicio:]
            raise
    object.__setattr__(estado, 'agenda', resultado)
    agenda._cambios.clear()


def sincronizar_pila(estado, pila):
    """Alta ordinaria de inversa en O(1) de serialización; resto usa diff general."""
    anterior = getattr(pila, '_proyeccion_cima', None)
    cima = pila._cima
    if (hasattr(pila, '_proyeccion_cima') and not getattr(pila, '_proyeccion_sucia', False)
            and cima is not None and cima.siguiente is anterior
            and len(pila) == len(estado.pila_deshacer)+1):
        valor = dato(cima.inversa)
        receptor = estado.__dict__.get('_registro')
        if receptor is not None and receptor.activo:
            inicio = len(receptor.registros)
            try:
                receptor.registrar_cambio(receptor.contexto(),
                    [['pila_deshacer'], True, [], True, [valor], 0])
            except Exception:
                del receptor.registros[inicio:]
                raise
        object.__setattr__(estado, 'pila_deshacer', [valor] + list(estado.pila_deshacer))
    else:
        sincronizar_secuencia(estado, 'pila_deshacer', pila.a_lista())
    pila._proyeccion_cima = cima
    pila._proyeccion_sucia = False
