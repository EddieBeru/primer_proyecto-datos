# Reglas de diseño de interfaz

Acuerdo del usuario,2026-11-10. Aplica a toda la interfaz Pygame, incluido código
existente. Complementa la guía de vista y las decisiones de estilo anteriores.
La corrección explícita de esquinas rectas tiene prioridad sobre cualquier nota
histórica que permita redondearlas.

## Tipografía

Base16 px. Los valores siguientes son decisiones del proyecto, no tamaños
mínimos impuestos por WCAG. Se evalúa el tamaño real al renderizar: reducir la
ventana no autoriza bajar de11 px ni convertir texto continuo en una caption.

| Rol | Tamaño base px | Peso real | Interlineado base px | Tracking |
| --- | ---: | ---: | ---: | ---: |
| H1 | 28 (24–32) | 700 | 36 | −0,02 em |
| H2 | 20 (18–20) | 600 | 28 | −0,01 em |
| H3/tarjeta | 16 | 600 | 24 | 0 |
| Cuerpo/datos | 16 (mínimo14) | 400 | 24 | 0 |
| Botón/pestaña | 14 | 600 | 20 | +0,01 em |
| Label | 14 | 500 | 20 | 0 |
| Auxiliar/badge | 12 (mínimo11) | 400/500 | 16 | +0,02 em |

El interlineado se redondea hacia arriba a múltiplos de4 px y nunca es menor
que la altura real de la fuente. La sugerencia de1,0–1,2 para botones no debe
recortar los glifos: el texto se centra dentro de un control con padding propio.
Logotipos decorativos pueden superar32 px; no se usa ese tamaño para menús o
texto corriente. Peso700 se reserva a títulos grandes/alertas críticas; no se
utilizan pesos100–300. El tracking de títulos se permite solamente mientras
no produzca colisiones. El tamaño de sprites sigue su escala de juego propia.

## Adaptación a Pygame

Los estilos se resuelven desde un único módulo compartido. Se usan archivos de
fuente legibles con variantes reales400/500/600/700, acompañados de su licencia,
para obtener los mismos resultados en todos los sistemas; fallback de sistema
legible si falta un archivo. Lato es la familia elegida para UI; su variante
incluida tiene dígitos del mismo ancho, verificados por métricas. Se conserva
el pixel-art del juego; no es necesario usar una fuente pixelada para los datos.

Pygame.font no recibe CSS `font-weight`, `letter-spacing` ni
`font-variant-numeric`. Se cargan las variantes de peso reales, se mide el
tracking en el renderizador y se comprueba el ancho de0–9. No se añaden nombres
de propiedades CSS sin efecto al código Python. Las fuentes y métricas se
cachean; no se cargan archivos en cada frame. No usar negrita sintética para
simular Medium/SemiBold si existe la variante real.

## Contraste, jerarquía y geometría

Texto normal:4.5:1 como mínimo. Texto grande:3:1 desde24 px regular o
aproximadamente18,67 px bold (19 px como umbral conservador). Los semibold
medianos se comprueban a4.5:1 para evitar depender de esa excepción. Los
colores se comprueban contra su fondo efectivo, incluidos hover, selección,
error y tooltip. La marca naranja se conserva para decoración; usar una
variante oscura para texto pequeño o fondos de botones con texto claro.

Esquinas rectas en paneles, campos, botones, barras y nodos. Espaciados/márgenes
con tokens de4/8/16/24/32 px. Trazos de1/2 px son válidos. Responder a falta de
espacio envolviendo, redistribuyendo o dando scroll; no comprimir todo el texto
ni escalar una captura completa de la pantalla. Foco visible y navegación por
teclado/ratón. Errores, estados vacíos y selecciones se entienden sin depender
solo del color.

## Nombres largos y acceso completo

Elipsis en etiquetas compactas, acompañada siempre de tooltip con el texto
completo al pasar el cursor. El mismo contenido está disponible al seleccionar
o enfocar con teclado, o en un detalle completo sin truncar. No cortar nombres
con `[:8]` ni reducir indefinidamente la fuente. Tooltips sobre panel opaco con
contraste suficiente, envoltura de palabras y límites de ventana; no capturan
el foco ni cambian el juego. Su contenido se conserva entre frames solo lo
necesario y se limpia al cambiar de pantalla/selección.

## Validación

Revisar inicio, selección, pausa, ajustes, controles, juego/HUD, mapa, historia,
fin/error;640×480,1024×800 y1280×720 como mínimo. Incluir nombres largos,
listas extensas, números que cambian, selección/hover y mensajes de error.
Pruebas significativas de métricas, contraste, truncamiento y acceso completo;
capturas revisadas para detectar solapes. Diferenciar revisión headless de
recorrido humano y no atribuir conformidad WCAG global a pruebas parciales.
Este es mantenimiento de presentación: flujo reducido con estas reglas y
criterios, sin crear una nueva capacidad del motor ni modificar contratos C1/C2.

Fuentes de referencia verificadas:
- [W3C: contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
- [Pygame-ce: fuentes, métricas y renderizado](https://pyga.me/docs/ref/font.html).
