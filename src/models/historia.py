"""Resumen histórico inmutable, compartido por consola y vista."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResumenHistorico:
    reloj: int
    accion: int
    sala_id: int
    sala_nombre: str
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    inventario: tuple[str, ...]
    efectos: tuple[tuple[str, int], ...]
    enemigos: tuple[tuple[str, str, int], ...]
    # (id, nombre/etiqueta, estado, ((dirección, destino, costo, estado), ...))
    mapa: tuple
    estado: str

    def texto(self):
        lineas = [f'Historia · t={self.reloj} · antes de acción #{self.accion}',
                  f'Sala {self.sala_id}: {self.sala_nombre}',
                  f'Vida {self.vida}/{self.vida_max} · ATQ {self.ataque} · DEF {self.defensa} · VEL {self.velocidad}',
                  'Inventario: ' + (', '.join(self.inventario) or 'Vacío'),
                  'Efectos: ' + (', '.join(f'{n}: {v}' for n,v in self.efectos) or 'Ninguno'),
                  'Enemigos: ' + (', '.join(f'{i} ({t}): {v}' for i,t,v in self.enemigos) or 'Ninguno'),
                  'Mapa conocido:']
        for sid, nombre, estado, salidas in self.mapa:
            lineas.append(f'  {sid}: {nombre} [{estado}]')
            for d, destino, costo, puerta in salidas:
                lineas.append(f'    {d} → {destino} · costo {costo} · {puerta}')
        return '\n'.join(lineas)
