# Propuesta de contrato neutral del esqueleto:001 y003

**Estado:** propuesta para revisión por los responsables de001/C1/C2, sin enmendar todavía CONTRATOS.md. Trazabilidad: FR-RES-01/02/03/05/06/11/12/14; FR-CAZ-01/02/10. Fuente única: `src/models/conocimiento.py` y DTO de transporte `src/models/rooms.py`.

## Superficie compartida

`preparar_metadatos` se amplía para devolver o conservar conjuntamente orden fuente inmutable e índice propio de salas, sin pérdida de campos. Mantener adaptador de la firma actual que consumen002, tests y ProveedorSesion; acordar la firma exacta al integrar, sin duplicar construcción en cada consumidor.

`DatosSalida(direccion, destino, costo, puerta_id, llave=None, cerrada_inicial=False)` conserva los cuatro campos actuales y añade defaults al final para compatibilidad. `DatosSala` conserva id, nombre y tupla de salidas en N,S,E,O. El contenedor común expone `salas_en_orden`, `sala(id)`, `salidas` e identidad física; no expone caché ni red. Los ordinales son internos y no sustituyen IDs en guardados.

`Exit.from_dict` conserva `costo`, default100; rechazar bool, cero, negativos o tipos incorrectos. Puerta cerrada sin llave es error de datos para003; no reinterpretarla como abierta. Para reciprocidad declarada y opuesta, costo, llave y estado inicial coinciden; reportar conflictos, no escoger silenciosamente un extremo. No exigir simetría donde la entrada solo declara un sentido.

## Responsabilidades

C1 obtiene páginas y valida transporte; el constructor neutral prepara una vez el plano completo e incidencias.001 consume costo, topología e identidad para reglas de terreno y puerta viva.003 usa topología/llave/estado inicial para verificación estática sin prioridades por costo.002 sigue consumiendo la proyección neutral y su conocimiento propio, sin recibir el mapa remoto como conocimiento observado. Ninguno declara un `Esqueleto003` alternativo.

La compilación común se ejecuta una sola vez por preparación y versión; su costo se contabiliza en la medición total local de003. La materialización inicial por páginas no es una búsqueda repetida tras cada llave. Compartir solo lecturas y estructura; no compartir marcas temporales de003 con búsquedas de001.

## Aceptación de integración

La misma instancia de datos preparados alimenta001 y003, con costo default100, costo1 y costos simétricos; ambos observan la misma llave y puerta física. Probar puertas paralelas, inversa ausente, IDs dispersos, orden de páginas y conflictos de reciprocidad. Coordinar ampliación de modelos/tests con001 antes de cambiar las firmas aprobadas en K1. Este plan no atribuye aprobación a otra persona.
