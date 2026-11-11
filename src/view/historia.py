"""Panel de historia: navegación y detalle visual sobre DTO inmutables de Sesión."""
import pygame
from src.view import paleta, texto
from src.view.medidas import medidas, ESPACIO, MARGEN


def coordenadas_historicas(mapa):
    coordenadas={}
    por_id={s[0]:s for s in mapa}
    vectores={'N':(0,-1),'S':(0,1),'E':(1,0),'O':(-1,0)}
    offset=0
    for sid,_,_,_ in mapa:
        if sid in coordenadas: continue
        coordenadas[sid]=(offset,0);cola=[sid];indice=0
        while indice<len(cola):
            origen=cola[indice];indice+=1
            cx,cy=coordenadas[origen]
            for direccion,destino,_,_ in por_id[origen][3]:
                if destino in por_id and destino not in coordenadas:
                    dx,dy=vectores[direccion]
                    punto=(cx+dx,cy+dy)
                    while punto in coordenadas.values(): punto=(punto[0]+1,punto[1])
                    coordenadas[destino]=punto;cola.append(destino)
        offset=max(q[0] for q in coordenadas.values())+2
    return coordenadas


class PanelHistoria:
    def __init__(self, sesion):
        self.sesion=sesion
        self.acciones=sesion.historial_disponible()
        self.indice=max(0,len(self.acciones)-1)
        self.modo='accion'
        self.entrada=str(len(self.acciones)) if self.acciones else '0'
        self.foco=0
        self.scroll=0
        self.seleccionar_texto=True
        self.lista_scroll=max(0,len(self.acciones)-8)
        self.error=''
        self.botones=[]
        self.coordenadas={}
        self.resumen=None
        self.consultar()

    def consultar(self):
        try:
            valor=int(self.entrada)
            r=self.sesion.historia_accion(valor) if self.modo=='accion' and self.acciones else self.sesion.historia(valor)
            self.resumen=r
            self.coordenadas=coordenadas_historicas(r.mapa)
            self.error=''
            self.scroll=0
            if self.modo=='accion' and self.acciones: self.indice=valor-1
        except ValueError as exc:
            self.error=str(exc)

    def seleccionar(self, indice):
        if not self.acciones: return
        self.indice=max(0,min(len(self.acciones)-1,indice))
        self.modo='accion'
        self.entrada=str(self.indice+1)
        self.consultar()
        self.seleccionar_texto=True
        self.lista_scroll=max(0,self.indice-4)

    def activar(self, accion):
        if accion=='cerrar': return False
        if accion=='entrada': self.foco=2;self.seleccionar_texto=True
        elif accion=='anterior': self.seleccionar(self.indice-1)
        elif accion=='siguiente': self.seleccionar(self.indice+1)
        elif accion in ('accion','tiempo'):
            self.modo=accion
            self.entrada=str(self.indice+1) if accion=='accion' and self.acciones else str(self.resumen.reloj if self.resumen else 0)
        elif accion=='consultar': self.consultar()
        elif isinstance(accion,int): self.seleccionar(accion)
        return True

    def evento(self, evento, pos=None):
        if evento.type==pygame.KEYDOWN:
            k=evento.key
            if k in (pygame.K_ESCAPE,pygame.K_h): return False
            if k==pygame.K_TAB: self.foco=(self.foco+(-1 if getattr(evento,'mod',0) & pygame.KMOD_SHIFT else 1))%6
            elif k in (pygame.K_RETURN,pygame.K_KP_ENTER):
                acciones=('accion','tiempo','consultar','anterior','siguiente','cerrar')
                return self.activar(acciones[self.foco])
            elif k==pygame.K_LEFT: self.seleccionar(self.indice-1)
            elif k==pygame.K_RIGHT: self.seleccionar(self.indice+1)
            elif k==pygame.K_UP: self.scroll=max(0,self.scroll-1)
            elif k==pygame.K_DOWN: self.scroll+=1
            elif k==pygame.K_BACKSPACE: self.entrada=self.entrada[:-1];self.foco=2
            elif getattr(evento,'unicode','') in '0123456789' and getattr(evento,'unicode',''):
                if self.foco!=2 or self.seleccionar_texto: self.entrada=''
                self.seleccionar_texto=False
                self.entrada=(self.entrada+evento.unicode)[:12];self.foco=2
        elif evento.type==pygame.MOUSEBUTTONDOWN and evento.button==1 and pos is not None:
            for rect,accion in self.botones:
                if rect.collidepoint(pos): return self.activar(accion)
        elif evento.type==pygame.MOUSEWHEEL:
            if pos is not None and pos[0]<self._limite_lista:
                self.lista_scroll=max(0,min(max(0,len(self.acciones)-1),self.lista_scroll-evento.y))
            else: self.scroll=max(0,self.scroll-evento.y*2)
        return True

    def dibujar(self, superficie, sprites):
        m=medidas(superficie);p=m.px
        fuente=m.fuente(14);chica=m.fuente(12);titulo=m.fuente(24,True)
        self.botones=[]
        velo=pygame.Surface(superficie.get_size(),pygame.SRCALPHA);velo.fill((62,39,26,155));superficie.blit(velo,(0,0))
        caja=superficie.get_rect().inflate(-p(MARGEN*2),-p(MARGEN*2))
        pygame.draw.rect(superficie,paleta.PANEL,caja)
        pygame.draw.rect(superficie,paleta.MURO,caja,m.trazo())
        x,y=caja.x+p(24),caja.y+p(16)
        superficie.blit(titulo.render('Historial de la partida',True,paleta.TEXTO),(x,y))
        superficie.blit(chica.render('Consulta el pasado · tu partida sigue en el presente',True,paleta.SECUNDARIO),(x,y+p(32)))
        def boton(rect,etiqueta,accion,seleccion=False,foco=None):
            pygame.draw.rect(superficie,paleta.TITULO if seleccion else paleta.FONDO_APP,rect)
            pygame.draw.rect(superficie,paleta.TEXTO if foco==self.foco else paleta.MURO,rect,m.trazo(2 if foco==self.foco else 1))
            imagen=chica.render(etiqueta,True,paleta.TEXTO_CLARO if seleccion else paleta.TEXTO)
            superficie.blit(imagen,imagen.get_rect(center=rect.center));self.botones.append((rect,accion))
        boton(pygame.Rect(caja.right-p(112),y,p(88),p(32)),'Esc  Cerrar','cerrar',foco=5)
        y+=p(64)
        boton(pygame.Rect(x,y,p(80),p(32)),'Acción','accion',self.modo=='accion',0)
        boton(pygame.Rect(x+p(88),y,p(80),p(32)),'Tiempo','tiempo',self.modo=='tiempo',1)
        campo=pygame.Rect(x+p(184),y,p(128),p(32))
        pygame.draw.rect(superficie,paleta.FONDO_APP,campo)
        pygame.draw.rect(superficie,paleta.TITULO if self.foco==2 else paleta.SECUNDARIO,campo,m.trazo(2))
        superficie.blit(fuente.render(('#' if self.modo=='accion' else 't=')+self.entrada,True,paleta.TEXTO),(campo.x+p(8),campo.y+p(8)))
        self.botones.append((campo,'entrada'))
        boton(pygame.Rect(x+p(320),y,p(88),p(32)),'Consultar','consultar',foco=2)
        boton(pygame.Rect(x+p(424),y,p(88),p(32)),'← Anterior','anterior',foco=3)
        boton(pygame.Rect(x+p(520),y,p(88),p(32)),'Siguiente →','siguiente',foco=4)
        if self.error: superficie.blit(chica.render(self.error,True,paleta.PELIGRO),(x,y+p(40)))
        y+=p(64)
        lista=pygame.Rect(x,y,p(184),caja.bottom-y-p(56))
        self._limite_lista=lista.right
        pygame.draw.rect(superficie,paleta.FONDO_APP,lista)
        superficie.blit(chica.render(f'ACCIONES · {len(self.acciones)}',True,paleta.SECUNDARIO),(lista.x+p(8),lista.y+p(8)))
        visibles=max(1,(lista.height-p(40))//max(1,p(40)))
        self.lista_scroll=min(self.lista_scroll,max(0,len(self.acciones)-visibles))
        if not self.acciones:
            superficie.blit(chica.render('Aún no hay acciones',True,paleta.SECUNDARIO),(lista.x+p(8),lista.y+p(40)))
        for fila,(n,t,tipo) in enumerate(self.acciones[self.lista_scroll:self.lista_scroll+visibles]):
            r=pygame.Rect(lista.x+p(8),lista.y+p(32)+fila*p(40),lista.width-p(16),p(32))
            boton(r,f'#{n} · t={t}'+(' · ↶' if tipo=='deshacer' else ''),n-1,n-1==self.indice)
        detalle=pygame.Rect(lista.right+p(24),y,caja.right-lista.right-p(48),lista.height)
        clip=superficie.get_clip();superficie.set_clip(detalle)
        if self.resumen:
            self._detalle(superficie,detalle,m,sprites)
        superficie.set_clip(clip)
        superficie.blit(chica.render('← → Acciones    Tab Foco    Números + Enter Consultar    ↑ ↓ / rueda Desplazar',True,paleta.SECUNDARIO),(x,caja.bottom-p(32)))

    def _detalle(self,sup,rect,m,sprites):
        p=m.px;r=self.resumen;f=m.fuente(14);ch=m.fuente(12);tit=m.fuente(18,True)
        x=rect.x;y=rect.y-p(self.scroll*24);w=rect.width
        def texto_linea(cadena,color=paleta.TEXTO,fuente=f):
            nonlocal y
            for linea in texto.envolver(cadena,fuente,w,100):
                sup.blit(fuente.render(linea,True,color),(x,y));y+=p(24)
        etiqueta=f'ANTES DE #{r.accion}' if self.modo=='accion' and self.acciones else 'CONSULTA POR TIEMPO' if self.acciones else 'INICIO DE PARTIDA'
        texto_linea(f'{etiqueta}   ·   TIEMPO {r.reloj}',paleta.TITULO,tit)
        texto_linea(f'Sala {r.sala_id} · {r.sala_nombre}')
        y+=p(8)
        bar=pygame.Rect(x,y,w,p(16));pygame.draw.rect(sup,paleta.VIDA_FONDO,bar)
        llena=bar.copy();llena.width=round(w*r.vida/max(1,r.vida_max));pygame.draw.rect(sup,paleta.VIDA,llena);y+=p(24)
        texto_linea(f'Vida {r.vida}/{r.vida_max}    ATQ {r.ataque}    DEF {r.defensa}    VEL {r.velocidad}')
        y+=p(8);texto_linea('INVENTARIO',paleta.TITULO,tit)
        if not r.inventario: texto_linea('Mochila vacía',paleta.SECUNDARIO)
        for item in r.inventario:
            imagen=pygame.transform.smoothscale(sprites.sprite(item),(p(24),p(24)))
            sup.blit(imagen,(x,y))
            etiqueta=texto.etiqueta_item(item)
            lineas=texto.envolver(etiqueta,f,max(1,w-p(32)),100)
            for i,linea in enumerate(lineas): sup.blit(f.render(linea,True,paleta.TEXTO),(x+p(32),y+i*p(24)))
            y+=p(32)+max(0,len(lineas)-1)*p(24)
        y+=p(8);texto_linea('EFECTOS Y ENEMIGOS',paleta.TITULO,tit)
        texto_linea(' · '.join(f'{n}: {v}' for n,v in r.efectos) or 'Sin efectos activos',paleta.SECUNDARIO)
        if not r.enemigos: texto_linea('Sin enemigos en esta sala',paleta.SECUNDARIO)
        for instancia,tipo,vida in r.enemigos: texto_linea(f'{instancia} · {tipo} · vida {vida}')
        y+=p(8);texto_linea('MAPA CONOCIDO EN ESTE INSTANTE',paleta.TITULO,tit)
        # Grafo histórico: conexiones y estados proceden solo del resumen elegido.
        coordenadas=self.coordenadas
        minx=min((q[0] for q in coordenadas.values()),default=0)
        maxx=max((q[0] for q in coordenadas.values()),default=0)
        miny=min((q[1] for q in coordenadas.values()),default=0)
        maxy=max((q[1] for q in coordenadas.values()),default=0)
        alto=max(p(96),(maxy-miny+1)*p(72))
        posiciones={sid:(x+p(32)+(cx-minx)*max(1,w-p(64))//max(1,maxx-minx),
                         y+p(32)+(cy-miny)*p(72)) for sid,(cx,cy) in coordenadas.items()}
        for sid,nombre,estado,salidas in r.mapa:
            for d,destino,costo,puerta in salidas:
                if destino in posiciones:
                    color=paleta.PUERTA_ABIERTA if puerta=='abierta' else paleta.PUERTA_LLAVE if puerta=='cerrada' else paleta.SECUNDARIO
                    pygame.draw.line(sup,color,posiciones[sid],posiciones[destino],m.trazo(2))
                    if puerta!='abierta':
                        marca=ch.render('×' if puerta=='cerrada' else '?',True,paleta.TEXTO)
                        punto=((posiciones[sid][0]+posiciones[destino][0])//2,
                               (posiciones[sid][1]+posiciones[destino][1])//2)
                        fondo=marca.get_rect(center=punto).inflate(p(8),p(8))
                        pygame.draw.rect(sup,paleta.PANEL,fondo)
                        sup.blit(marca,marca.get_rect(center=punto))
        for sid,nombre,estado,salidas in r.mapa:
            centro=posiciones[sid];nodo=pygame.Rect(0,0,p(56),p(40));nodo.center=centro
            pygame.draw.rect(sup,paleta.TITULO if sid==r.sala_id else paleta.PANEL,nodo)
            pygame.draw.rect(sup,paleta.MURO,nodo,m.trazo(2 if sid==r.sala_id else 1))
            etiqueta=texto.envolver(f'#{sid}'+(' ?' if estado=='avistada' else ''),ch,nodo.width-p(8),1)[0]
            imagen=ch.render(etiqueta,True,paleta.TEXTO_CLARO if sid==r.sala_id else paleta.TEXTO)
            sup.blit(imagen,imagen.get_rect(center=centro))
        y+=alto+p(8)
        texto_linea('Línea: abierta · ×: cerrada · ?: sin observar',paleta.SECUNDARIO,ch)
        # Detalle de las mismas salas, sin acceder al mapa presente ni plano oculto.
        for sid,nombre,estado,salidas in r.mapa:
            lineas=texto.envolver(f'#{sid}  {nombre} · {estado}',ch,w-p(32),100)
            detalle_salidas=[]
            for d,destino,costo,estado_puerta in salidas:
                detalle_salidas.extend(texto.envolver(f'{d} → #{destino} · {costo} · {estado_puerta}',ch,w-p(32),100))
            alto=p(24*(len(lineas)+len(detalle_salidas))+16)
            caja=pygame.Rect(x,y,w,alto)
            pygame.draw.rect(sup,paleta.FONDO_APP,caja)
            pygame.draw.rect(sup,paleta.TITULO if sid==r.sala_id else paleta.SECUNDARIO,caja,m.trazo())
            for linea in lineas:
                sup.blit(ch.render(linea,True,paleta.TEXTO),(x+p(8),y+p(8)));y+=p(24)
            for linea in detalle_salidas:
                sup.blit(ch.render(linea,True,paleta.SECUNDARIO),(x+p(16),y+p(8)));y+=p(24)
            y+=p(24)
        self.scroll_max=max(0,(y+p(self.scroll*24)-rect.bottom+p(24))//max(1,p(24)))
        self.scroll=min(self.scroll,self.scroll_max)
