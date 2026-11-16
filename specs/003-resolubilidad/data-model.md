# Modelo de datos003

Todas las ampliaciones de interfaz son propuestas; ver [contratos](contracts/interfaces.md). Se comparte [el esqueleto](contracts/esqueleto-compartido.md) con001, sin duplicarlo.

## Esqueleto común — FR-RES-01/02/03/12

- `Exit` de transporte: sala destino, cerrada(default falso), llave opcional, cierre automático opcional, costo entero≥1(default100). JSON solo en frontera.
- `DatosSalida` neutral e inmutable: dirección, destino, costo, puerta_id; añadir `llave: str|None` y `cerrada_inicial: bool`, con defaults compatibles para consumidores actuales. No añadir conocimiento ni estado mutable de partida.
- `DatosSala`: id, nombre, salidas N,S,E,O; colección fuente inmutable preserva orden de páginas y salas, además de `TablaIndice` para consulta. Una sola instancia del modelo preparado se entrega a001/003 y al proveedor de002.
- `puerta_id=(sala,dirección)` canónico ya aprobado para extremos recíprocos opuestos; no unificar puertas paralelas ni crear inversas. Costos/llave/estado recíprocos deben ser coherentes; conflicto es error de datos. El reporte enumera extremos salientes de frontera, sin duplicar ni perder la dirección.

## Ubicaciones de llaves — FR-RES-02/11/14

`UbicacionesLlaves`: id de cripta, versión, indicador de respuesta completa y secuencia de ubicaciones en orden declarado. `UbicacionLlave`: id de llave, sala, enemigo opcional. El enemigo es identificador de instancia, y sala es su inicio; no se consultan sus movimientos ni ficha.

Identidad por id de llave, ordinal por primera aparición. Varias ubicaciones del mismo id son alternativas: basta alcanzar una, la llave aparece una sola vez; conservar todas para diagnóstico. El tamaño L cuenta registros de ubicación y no solo ids únicos. Si la respuesta tiene una ubicación por llave, L=K. Sala desconocida o versión distinta es error; ausencia de un id requerido en una respuesta completa crea una llave sintética no obtenible con ubicación no declarada. Respuesta ausente/incompleta no equivale a ausencia de llaves.

## Estado de verificación — FR-RES-04/05/06/07/12

Ordinales compactos0..n−1, nunca arreglos dimensionados por max(id). Arreglos por sala: descubierta, procesada, testigo de entrada. Por llave: obtenida, primer ordinal de ubicación accesible, posición en orden de obtención, inicio/fin de pendientes. Por salida: ordinal fuente, primera identificación, llave requerida y estado habilitada/bloqueada; por regla: consecuencia, premisas, pendientes. Suscriptores: lista por hecho, incidencias de tamaño constante. Las llaves usan la ampliación textual del índice neutral con hash UTF8 propio FNV-1a64 y verificación de igualdad completa; no recorrer cubetas para determinar orden.

Reglas:

- Abierta: alcanzable(origen) → alcanzable(destino).
- Cerrada: alcanzable(origen) Y obtenida(llave) → alcanzable(destino).
- Ubicación: alcanzable(sala_inicial_de_la_ubicación) → obtenida(llave).

Múltiples reglas para la misma consecuencia son alternativas OR. Conservar esa distinción; no producir todas las parejas entre llaves de un camino.

Transiciones: `preparando → incompleta | propagando → resumiendo → resoluble | no_resoluble`. Un hecho se activa una sola vez. Descubrimiento y procesamiento de sala son estados distintos: solo el procesamiento, después de las llaves locales, permite activar sus reglas salientes N,S,E,O. La compilación registra incidencias pero no enlaza todavía puertas a pendientes en orden fuente; se enlazan al identificarlas durante el avance. El estado inicial o falso no se interpreta como prueba hasta terminar la propagación. Verificación no cambia reloj, RNG, inventario, puertas vivas, conocimiento ni contenido descargado.

## Evidencia residual — FR-RES-06/07/12/15

Reutiliza reglas, incidencias y etiquetas compiladas del mismo recorrido. Conclusión falsa→regla alternativa→premisas falsas. Una puerta puede tener dos premisas falsas; registrar ambas, no elegir una arbitrariamente perdiendo otra alternativa. Las incidencias inversas necesarias para análisis se guardan durante compilación; no se relee el esqueleto para construir el diagnóstico.

Un circuito debe contener llave, ubicación y puerta que requiere una llave inaccesible. Un ciclo abierto de salas desconectadas sin llaves no califica. Testigo no contiene todos los caminos posibles: se conservan reglas e incidencias compartidas, cada una emitida como máximo una vez, con referencias por ordinal. Así las alternativas no expanden exponencialmente el reporte.

## Resultado/DTO — FR-RES-03/06/07/08/09/10/14/15

`ResultadoResolubilidad`: id, versión, estado, razones de condiciones de victoria incumplidas, orden_llaves, llaves_no_obtenibles, frontera, ubicaciones, ciclo opcional, alternativas_bloqueadas y contadores opcionales de medición. Colecciones inmutables, IDs completos; no exponer estado vivo ni tabla mutable.

- Resoluble exige `llave_salida` obtenida y al menos una salida declarada hacia `sala_salida` que la requiere, con origen alcanzable y acceso posible; no basta marcar la sala final alcanzable por otra entrada.
- Frontera final: salida cerrada de origen alcanzable a destino no alcanzable, llave no obtenida. Revisar las evidencias pendientes finales una vez; no confundir frontera inicial con final ni incluir puertas internas a región alcanzable.
- No resoluble enumera todas las llaves no obtenibles, incluidas requeridas sin ubicación; no exige conseguir llaves opcionales para declarar victoria.
- Incompleta transporta error preciso y ninguna afirmación binaria. No puede forzarse.
- `texto_reporte(resultado)` conserva formato FR-RES-15 e incluye el ciclo y las demás alternativas bloqueadas con sus causas. Para detalles compartidos, una sola línea por evidencia y referencias estables; no expandir caminos por llave.

## Persistencia/compatibilidad — FR-RES-11/14

Caché de ubicación versionada independiente; encabezado con versión de formato1, id y versión de cripta. Validar forma, integridad, cobertura y orden antes de publicar/usar. Mismatch invalida; no mezclar plano y ubicaciones de versiones diferentes. No hay cambios al guardado v4 ni bitácora. Paquetes offline anteriores sin archivo de llaves fallan explícitamente al verificar una nueva partida, sin inventar ubicaciones. El flujo de cargar/replay legado no consulta este insumo nuevo.
