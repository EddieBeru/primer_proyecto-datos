"""Conocimiento incremental y deltas por registro; nunca consulta contenido."""

from __future__ import annotations

from dataclasses import dataclass

from src.estructuras.tabla_indice import TablaIndice
from src.models.conocimiento import DatosSala, DatosSalida, Extremo, DIRECCIONES


@dataclass(frozen=True, slots=True)
class SalaConocida:
    id: int
    estado: str
    nombre: str | None = None
    salidas: tuple[DatosSalida, ...] = ()


@dataclass(frozen=True, slots=True)
class CambioConocimiento:
    tipo: str
    clave: int | Extremo
    antes: SalaConocida | bool | None
    despues: SalaConocida | bool | None

    def a_dict(self):
        return {"tipo": self.tipo, "clave": list(self.clave) if self.tipo == "puerta" else self.clave,
                "antes": _registro(self.antes), "despues": _registro(self.despues)}

    @classmethod
    def desde_dict(cls, dato):
        tipo = dato["tipo"]
        if tipo not in ("sala", "puerta"):
            raise ValueError("tipo de delta de conocimiento inválido")
        clave = tuple(dato["clave"]) if tipo == "puerta" else dato["clave"]
        # El índice valida también la forma de la clave.
        TablaIndice()[clave] = True
        antes, despues = _leer_registro(dato["antes"]), _leer_registro(dato["despues"])
        for registro in (antes, despues):
            if registro is not None and ((tipo == "sala" and (not isinstance(registro, SalaConocida) or registro.id != clave))
                                         or (tipo == "puerta" and type(registro) is not bool)):
                raise ValueError("registro de delta incompatible con su clave")
        return cls(tipo, clave, antes, despues)


def _registro(valor):
    if not isinstance(valor, SalaConocida):
        return valor
    resultado = {"id": valor.id, "estado": valor.estado}
    if valor.estado == "explorada":
        resultado["nombre"] = valor.nombre
        resultado["salidas"] = [{"direccion": s.direccion, "destino": s.destino,
            "costo": s.costo, "puerta_id": [s.puerta_id[0], s.puerta_id[1]]} for s in valor.salidas]
    return resultado


def _leer_registro(dato):
    if dato is None or type(dato) is bool:
        return dato
    if type(dato) is not dict or type(dato.get("id")) is not int:
        raise ValueError("registro de sala inválido")
    if dato.get("estado") == "avistada" and tuple(dato.keys()) in (("id", "estado"), ("estado", "id")):
        return SalaConocida(dato["id"], "avistada")
    if dato.get("estado") != "explorada" or type(dato.get("salidas")) is not list:
        raise ValueError("estado de conocimiento inválido")
    salidas = tuple(DatosSalida(s["direccion"], s["destino"], s["costo"], tuple(s["puerta_id"])) for s in dato["salidas"])
    sala = DatosSala(dato["id"], dato["nombre"], salidas)
    return SalaConocida(sala.id, "explorada", sala.nombre, sala.salidas)


class MapaConocido:
    def __eq__(self, otro):
        if not isinstance(otro, MapaConocido):
            return NotImplemented
        return (len(self._salas) == len(otro._salas) and len(self._puertas) == len(otro._puertas)
                and all(otro._salas.obtener(k) == v for k,v in self._salas.items())
                and all(otro._puertas.obtener(k) == v for k,v in self._puertas.items()))

    def __init__(self):
        self._salas: TablaIndice[SalaConocida] = TablaIndice()
        self._puertas: TablaIndice[bool] = TablaIndice()
        self.revision = 0

    def sala(self, sala_id):
        return self._salas.obtener(sala_id)

    def puerta(self, puerta_id):
        valor = self._puertas.obtener(puerta_id)
        return "desconocida" if valor is None else ("cerrada" if valor else "abierta")

    def salas(self):
        return self._salas.valores()

    def _cambiar(self, tipo, clave, valor):
        tabla = self._salas if tipo == "sala" else self._puertas
        antes = tabla.obtener(clave)
        if antes == valor:
            return []
        cambio = CambioConocimiento(tipo, clave, antes, valor)
        self.aplicar(cambio)
        return [cambio]

    def aplicar(self, cambio, adelante=True):
        tabla = self._salas if cambio.tipo == "sala" else self._puertas
        valor = cambio.despues if adelante else cambio.antes
        if valor is None:
            tabla.borrar(cambio.clave)
        else:
            tabla[cambio.clave] = valor
        self.revision += 1

    def avistar(self, sala_id):
        if sala_id in self._salas:
            return []
        return self._cambiar("sala", sala_id, SalaConocida(sala_id, "avistada"))

    def explorar(self, datos: DatosSala):
        cambios = self._cambiar("sala", datos.id, SalaConocida(datos.id, "explorada", datos.nombre, datos.salidas))
        for salida in datos.salidas:
            cambios.extend(self.avistar(salida.destino))
        return cambios

    def revelar(self, sala_id, datos_sala, antorcha=False):
        datos = datos_sala(sala_id)
        cambios = self.explorar(datos)
        if antorcha:
            for salida in datos.salidas:
                cambios.extend(self.explorar(datos_sala(salida.destino)))
        return cambios

    def observar(self, puerta_id, cerrada):
        if type(cerrada) is not bool:
            raise TypeError("estado de puerta debe ser booleano")
        return self._cambiar("puerta", puerta_id, cerrada)

    def adyacentes(self, sala_id):
        sala = self.sala(sala_id)
        if sala is None or sala.estado != "explorada":
            return
        for direccion in DIRECCIONES:
            for salida in sala.salidas:
                destino = self.sala(salida.destino)
                if salida.direccion == direccion and destino is not None and destino.estado == "explorada" \
                        and self.puerta(salida.puerta_id) == "abierta":
                    yield salida

    def a_dict(self):
        return {"salas": [_registro(s) for s in self._salas.valores()],
                "puertas": [{"sala_id": k[0], "direccion": k[1], "cerrada": v} for k,v in self._puertas.items()]}

    @classmethod
    def desde_dict(cls, dato, datos_sala=None):
        if type(dato) is not dict or type(dato.get("salas")) is not list or type(dato.get("puertas")) is not list:
            raise ValueError("conocimiento ausente o inválido")
        mapa = cls()
        for registro in dato["salas"]:
            sala = _leer_registro(registro)
            if not isinstance(sala, SalaConocida) or sala.id in mapa._salas:
                raise ValueError("sala de conocimiento inválida o duplicada")
            if datos_sala is not None:
                datos = datos_sala(sala.id)
                if sala.estado == "explorada" and (datos.nombre != sala.nombre or datos.salidas != sala.salidas):
                    raise ValueError("conocimiento no coincide con metadatos")
            mapa._salas[sala.id] = sala
        for registro in dato["puertas"]:
            clave = (registro["sala_id"], registro["direccion"])
            cerrada = registro["cerrada"]
            if type(cerrada) is not bool or clave in mapa._puertas:
                raise ValueError("memoria de puerta inválida o duplicada")
            if datos_sala is not None:
                datos = datos_sala(clave[0])
                if not any(s.puerta_id == clave for s in datos.salidas):
                    raise ValueError("referencia de puerta inválida")
            mapa._puertas[clave] = cerrada
        for sala in mapa.salas():
            for salida in sala.salidas:
                if mapa.sala(salida.destino) is None:
                    raise ValueError("destino conocido sin registro avistado/explorado")
        return mapa
