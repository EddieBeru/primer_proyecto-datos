"""Historia por diario de escrituras y checkpoints; consultas sin motor ni red."""
from copy import deepcopy
from src.controller2.registro_mutaciones import dato, diferencias, enlazar, copiar_registro
from src.models.historia import ResumenHistorico

def conocimiento_serializado(estado):
    from src.controller2.orden_local import insercion
    c = estado.conocimiento.a_dict()
    c['salas'] = insercion(c['salas'], clave=lambda r: r['id'])
    c['puertas'] = insercion(c['puertas'], clave=lambda r: (r['sala_id'],r['direccion']))
    return c


def estado_serializado(estado):
    raiz = dato(estado.a_dict())
    raiz['conocimiento'] = conocimiento_serializado(estado)
    return raiz


CHECKPOINT_CADA = 20  # elegido por bench_historia; véase DECISIONES.md


def aplicar(raiz, cambio, adelante=False, verificar=False):
    ruta, pa, antes, pd, despues = cambio[:5]
    objeto = raiz
    for k in ruta[:-1]: objeto = objeto[k]
    k = ruta[-1]
    presente, valor = (pd, despues) if adelante else (pa, antes)
    if verificar:
        esperado_presente, esperado = (pa, antes) if adelante else (pd, despues)
        if len(cambio)==6:
            inicio=cambio[5]
            if type(inicio) is not int or inicio<0 or type(esperado) is not list or objeto[k][inicio:inicio+len(esperado)] != esperado:
                raise ValueError('segmento histórico incoherente')
        elif isinstance(objeto,dict):
            if (k in objeto) != esperado_presente or (esperado_presente and objeto[k] != esperado):
                raise ValueError('delta histórico incoherente')
        elif not esperado_presente or objeto[k] != esperado:
            raise ValueError('delta histórico incoherente')
    if len(cambio) == 6:
        lista = objeto[k]
        segmento = antes if adelante else despues
        inicio = cambio[5]
        lista[inicio:inicio+len(segmento)] = deepcopy(valor)
    elif presente:
        objeto[k] = deepcopy(valor)
    else:
        del objeto[k]


class LineaTiempo:
    def __init__(self, estado, k=CHECKPOINT_CADA):
        if type(k) is not int or k < 1: raise ValueError('K debe ser entero ≥1')
        self.k = k
        self.registros = []
        self.acciones = []  # (posición inicial, tiempo, tipo)
        self.cortes = []   # (tiempo, posición tras evento, ordinal)
        self.checkpoints = []  # (posición, ordinal, estado)
        self.activo = False
        self.estado = estado
        self._inicio = 0
        self._conocimiento = conocimiento_serializado(estado)
        self.checkpoints.append([0, 0, estado_serializado(estado)])
        enlazar(estado, self)

    def presencia(self, ruta, pa, antes, pd, despues):
        if self.activo:
            self.registrar_cambio(self.contexto(), [list(ruta), pa, antes, pd, despues])

    def cambio(self, ruta, antes, despues):
        if self.activo:
            pendientes = list(diferencias(antes, despues, ruta))
            inicio = len(self.registros)
            try:
                for cambio in pendientes: self.registrar_cambio(self.contexto(), cambio)
            except Exception:
                del self.registros[inicio:]
                raise

    def contexto(self):
        return {'reloj':self._tiempo,'fase':self._fase,
                'orden':len(self.registros),'ordinal':len(self.acciones)+1}

    def registrar_cambio(self, contexto, inversa):
        """Registro interno ya desligado del estado vivo."""
        if not self.activo: raise ValueError('sin acción abierta')
        self.registros.append(copiar_registro(inversa))

    def comenzar(self):
        self._tiempo = self.estado.reloj
        self._fase = "accion"
        self.activo = True
        self._inicio = len(self.registros)
        self._cortes_inicio = len(self.cortes)
        self._acciones_inicio = len(self.acciones)
        self._checkpoints_inicio = len(self.checkpoints)

    def conocimiento(self):
        nuevo = conocimiento_serializado(self.estado)
        self.cambio(('conocimiento',), self._conocimiento, nuevo)
        self._conocimiento = nuevo

    def evento(self):
        self.conocimiento()
        self.cortes.append([self.estado.reloj, len(self.registros), len(self.acciones)+1])

    def cerrar_accion(self, contexto, estado):
        self.conocimiento()
        self.activo = False
        if len(self.registros) == self._inicio:
            del self.cortes[self._cortes_inicio:]
            return
        self.acciones.append([self._inicio, contexto['reloj'], contexto.get('tipo','accion')])
        if len(self.acciones) % self.k == 0:
            self.checkpoints.append([len(self.registros), len(self.acciones), estado_serializado(estado)])

    def revertir(self):
        """Solo en error: reconstruir el inicio desde deltas/checkpoint, sin snapshot de transacción."""
        self.activo = False
        anterior = self.reconstruir(self._inicio)
        del self.acciones[self._acciones_inicio:]
        del self.checkpoints[self._checkpoints_inicio:]
        self.descartar()
        return anterior

    def descartar(self):
        self.activo = False
        del self.registros[self._inicio:]
        del self.cortes[self._cortes_inicio:]

    def truncar_intervalo(self, contexto):
        """Elimina solo el sufijo del último intervalo ordinario, incluso tras scrolls."""
        self.activo = False
        i = len(self.acciones)-1
        while i >= 0 and self.acciones[i][2] == 'deshacer': i -= 1
        if i < 0: raise ValueError('intervalo histórico inexistente')
        pos, tiempo, _ = self.acciones[i]
        anterior = self.reconstruir(pos)
        # Preparar el reemplazo antes de tocar la rama publicada. Solo se retiene
        # temporalmente el sufijo afectado, nunca una copia de toda la historia.
        nuevos = list(diferencias(anterior, estado_serializado(self.estado)))
        corte = len(self.cortes)
        while corte and self.cortes[corte-1][1] > pos: corte -= 1
        cp = len(self.checkpoints)
        while cp>1 and self.checkpoints[cp-1][1] > i: cp -= 1
        sufijos = (self.acciones[i:], self.registros[pos:], self.cortes[corte:], self.checkpoints[cp:])
        limites = (self._inicio,self._cortes_inicio)
        try:
            del self.acciones[i:]
            del self.registros[pos:]
            del self.cortes[corte:]
            del self.checkpoints[cp:]
            self._inicio = pos
            self._cortes_inicio = corte
            self.activo = True
            self.registros.extend(nuevos)
            self._conocimiento = conocimiento_serializado(self.estado)
            self.cerrar_accion({'reloj': tiempo, 'tipo':'deshacer'}, self.estado)
        except Exception:
            self.acciones[i:] = sufijos[0]
            self.registros[pos:] = sufijos[1]
            self.cortes[corte:] = sufijos[2]
            self.checkpoints[cp:] = sufijos[3]
            self._inicio,self._cortes_inicio=limites
            raise

    def reconstruir(self, posicion):
        # Primer checkpoint posterior: búsqueda binaria propia.
        izq, der = 0, len(self.checkpoints)
        while izq < der:
            m = (izq+der)//2
            if self.checkpoints[m][0] < posicion: izq=m+1
            else: der=m
        if izq < len(self.checkpoints):
            fin, ordinal, raiz = self.checkpoints[izq]
            raiz = deepcopy(raiz)
        else:
            fin, ordinal, raiz = len(self.registros), len(self.acciones), estado_serializado(self.estado)
        izq, der = 0, len(self.acciones)
        while izq < der:
            m = (izq+der)//2
            if self.acciones[m][0] <= posicion: izq=m+1
            else: der=m
        self.ultimos_deltas = fin-posicion
        self.ultimas_acciones = 0 if fin==posicion else ordinal-max(0,izq-1)
        for i in range(fin-1, posicion-1, -1): aplicar(raiz, self.registros[i])
        return raiz

    def corte_tiempo(self, t):
        if type(t) is not int or t<0 or t>self.estado.reloj:
            raise ValueError('Tiempo histórico inválido o futuro.')
        izq, der=0,len(self.acciones)
        while izq<der:
            m=(izq+der)//2
            if self.acciones[m][1]<t: izq=m+1
            else: der=m
        if izq<len(self.acciones) and self.acciones[izq][1]==t:
            return self.acciones[izq][0], izq+1
        izq,der=0,len(self.cortes)
        while izq<der:
            m=(izq+der)//2
            if self.cortes[m][0]<=t: izq=m+1
            else: der=m
        if izq: return self.cortes[izq-1][1], self.cortes[izq-1][2]+1
        return 0,1

    def consultar(self, t=None, accion=None):
        if accion is not None:
            if type(accion) is not int or not 1<=accion<=len(self.acciones):
                raise ValueError('Acción histórica inexistente.')
            pos=self.acciones[accion-1][0]
            reloj=self.acciones[accion-1][1]
        else:
            pos,accion=self.corte_tiempo(t)
            reloj=t
        return resumen(self.reconstruir(pos), reloj, accion)

    def a_dict(self):
        return deepcopy({'version':1,'k':self.k,'acciones':self.acciones,
            'cortes':self.cortes,'registros':self.registros,'checkpoints':self.checkpoints})

    @classmethod
    def desde_dict(cls, data, estado, datos_sala=None):
        if type(data) is not dict or type(data.get('version')) is not int or data.get('version') != 1: raise ValueError('historia incompatible')
        linea=cls(estado, data['k'])
        for campo in ('acciones','cortes','registros','checkpoints'):
            if type(data.get(campo)) is not list: raise ValueError('historia malformada')
            setattr(linea,campo,deepcopy(data[campo]))
        if not linea.checkpoints or linea.checkpoints[0][:2] != [0,0]: raise ValueError('origen histórico ausente')
        if len(linea.checkpoints) != len(linea.acciones)//linea.k+1:
            raise ValueError('frecuencia de checkpoints inválida')
        prev=(-1,-1)
        for pos,t,tipo in linea.acciones:
            if type(pos) is not int or type(t) is not int or pos<prev[0] or t<0 or t<prev[1] or not 0<=pos<=len(linea.registros) or t>estado.reloj or tipo not in ('accion','deshacer'):
                raise ValueError('corte de acción inválido')
            prev=pos,t
        prev=(-1,-1)
        for t,pos,ordinal in linea.cortes:
            if type(t) is not int or type(pos) is not int or type(ordinal) is not int or t<0 or t<prev[0] or pos<prev[1] or not 0<=pos<=len(linea.registros) or not 1<=ordinal<=len(linea.acciones) or t>estado.reloj:
                raise ValueError('corte temporal inválido')
            prev=t,pos
        for i,(pos,ordinal,raiz) in enumerate(linea.checkpoints):
            if type(ordinal) is not int or ordinal != i*linea.k or ordinal>len(linea.acciones) or type(pos) is not int or not 0<=pos<=len(linea.registros) or type(raiz) is not dict:
                raise ValueError('checkpoint inválido')
            esperado = linea.acciones[ordinal][0] if ordinal<len(linea.acciones) else len(linea.registros)
            if ordinal == 0: esperado = 0
            if pos != esperado: raise ValueError('posición de checkpoint inválida')
        for c in linea.registros:
            if type(c) is not list or len(c) not in (5,6) or type(c[0]) is not list or not c[0] or any(type(k) not in (int,str) or (type(k) is int and k<0) for k in c[0]) or type(c[1]) is not bool or type(c[3]) is not bool:
                raise ValueError('delta histórico inválido')
        # Validar cadena completa, referencias y contenido de checkpoints antes de instalar.
        raiz=estado_serializado(estado)
        cp=len(linea.checkpoints)-1
        for pos in range(len(linea.registros),-1,-1):
            if cp>=0 and linea.checkpoints[cp][0]==pos:
                if raiz != linea.checkpoints[cp][2]: raise ValueError('checkpoint incoherente')
                from src.controller2.modelo import EstadoPartida
                from src.controller2.conocimiento import MapaConocido
                candidato=EstadoPartida.desde_dict(deepcopy(raiz))
                if candidato.sala_actual not in candidato.salas:
                    raise ValueError('sala histórica inexistente')
                MapaConocido.desde_dict(raiz['conocimiento'],datos_sala)
                cp-=1
            if pos: aplicar(raiz,linea.registros[pos-1],verificar=True)
        return linea


def resumen(raiz, reloj, accion):
    from src.controller2.conocimiento import MapaConocido
    conocimiento=MapaConocido.desde_dict(raiz['conocimiento'])
    mapa=[]
    for sala in conocimiento.salas():
        salidas=tuple((s.direccion,s.destino,s.costo,conocimiento.puerta(s.puerta_id)) for s in sala.salidas)
        mapa.append((sala.id,sala.nombre or 'Sala avistada',sala.estado,salidas))
    from src.controller2.orden_local import insercion
    mapa=insercion(mapa,clave=lambda s:s[0])
    j=raiz['jugador'];s=raiz['salas'][str(raiz['sala_actual'])]
    return ResumenHistorico(reloj,accion,raiz['sala_actual'],s['nombre'],j['vida_actual'],j['vida_max'],j['ataque'],j['defensa'],j['velocidad'],tuple(j['inventario']),tuple(j['efectos'].items()),tuple((e['instancia'],e['tipo_id'],e['vida_actual']) for e in s['enemigos']),tuple(mapa),raiz['estado'])
