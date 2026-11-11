"""Observación de escrituras del modelo; conserva cambios, nunca snapshots por acción."""
from dataclasses import fields, is_dataclass


def dato(valor):
    if is_dataclass(valor):
        return {f.name: dato(getattr(valor, f.name)) for f in fields(valor)}
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
    if is_dataclass(valor):
        return {f.name: limpio(getattr(valor,f.name)) for f in fields(valor)}
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
