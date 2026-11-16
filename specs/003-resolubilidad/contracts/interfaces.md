# Contratos propuestos003

**Estado:** propuesta concreta para revisión; no se ha modificado CONTRATOS.md ni se atribuye aprobación al compañero. La autorización «pues hazlo» corresponde a la semántica de ciclos; no firma estos contratos nuevos. Implementar cambios K1/K5 después del acuerdo de regla6.3. La preparación del diseño no necesita ejecutar HTTP ni publicar cambios.

## API de ubicaciones — FR-RES-01/02/11/14

Propuesta de recurso por cripta: `GET /criptas/{cripta_id}/llaves`. Es el nuevo `/llaves` solicitado, bajo el prefijo de cripta usado por el API actual. Respuesta propuesta, no confirmada en un servidor:

```json
{
  "cripta_id": "cripta-01",
  "version_cripta": "a3f91c",
  "completa": true,
  "llaves": [
    {"id": "itm_llave_bronce", "sala": 2, "enemigo": null},
    {"id": "itm_llave_negra", "sala": 7, "enemigo": "e-701"}
  ]
}
```

Orden de `llaves` significativo y persistido. `enemigo` identifica instancia; `sala` siempre es su sala inicial cuando el enemigo suelta la llave. El endpoint no devuelve posiciones posteriores ni exige descargar catálogo/contenido. Varias ubicaciones del mismo id son alternativas y conservan orden. Respuesta completa sin un id requerido implica no obtenible/ubicación no declarada; lista vacía válida no equivale a404, fallo de red o `completa:false`. Validar tipos estrictos, salas existentes, id/version coherentes y `completa:true`. JSON es transporte, no índice del cálculo.

C1 expone `ubicaciones_llaves(cripta_id, budget, version_cripta)` al preparador. Usa el mismo mecanismo de solicitudes/reintentos ya existente: gastar antes de cada intento,429 espera real sin avanzar reloj, máximo vigente de intentos; cero intentos si no hay presupuesto.404/500/forma inválida/red/mismatch se traducen a verificación incompleta. No rescatar descargando todos los contenidos.

Persistencia opcional C1: `llaves_<id>.json` en paquete offline y caché local con versión de formato1, id, versión y respuesta completa. El backend offline lee el mismo contrato sin gastar red. Escritura temporal y reemplazo atómico, validar antes de publicar; no leer datos obsoletos como actuales. Una lectura local válida cuesta cero solicitudes. Confirmar la versión con datos generales ya obtenidos, sin una petición de versión redundante; si se realiza otra validación remota, también cuenta. Paquete antiguo sin archivo produce error explícito solo en el nuevo flujo de verificación.

El presupuesto nace una sola vez en preparación, contabiliza bootstrap y lista realmente realizada y continúa en la partida si inicia. Hoy `iniciar_cripta(contar_lista=True)` puede descontar una lista no ejecutada; pasar el número real de solicitudes previas, o usar `contar_lista=False` en `--verificar <id>` directo. No reiniciar el contador ni permitir excepciones silenciosas si el presupuesto no alcanza. En frío: solicitudes de datos generales + páginas del esqueleto + `/llaves`, con cada reintento; después solo si inicia, catálogo y contenido. Verificación no necesita esos dos últimos.

## Modelo común K1 — FR-RES-01/02/03/05/11/12/14

Ver [contrato único del esqueleto](esqueleto-compartido.md);001 y003 comparten DTO, constructor e identidad de puerta. No hay copia divergente003.

## Algoritmo puro — FR-RES-01–07/12/14/15

Propuesta `verificar_resolubilidad(info, esqueleto_preparado, ubicaciones, medir=False) -> ResultadoResolubilidad`. Sin C1, HTTP, Pygame, reloj de juego, catálogo ni estado vivo. Los tipos neutrales se importan desde `src/models`; las estructuras desde `src/estructuras`. Resultado inmutable y formateador compartido `texto_reporte(resultado) -> str`, con formato FR-RES-15 y evidencias de alternativas. Contadores optativos no cambian orden ni semántica.

## Sesión K5 y ciclo de inicio — FR-RES-08/09/10/11/14/15

Preparación separada: `preparar_inicio(id) -> PreparacionInicio` contiene resultado, plano común, ubicaciones, info y budget. No crea EstadoPartida/Fachada/bitácora ni activa enemigos. `iniciar(id, semilla=0, forzar=False)` consume esa preparación una sola vez: si no resoluble y no forzar, no crea partida; conserva resultado para consulta y comunica bloqueo mediante error tipado que transporta el DTO. Si incompleta, error tipado equivalente sin posibilidad de forzar. Para inicio permitido mantiene retorno `FotoEstado` existente y expone `reporte_inicio()` con el DTO; no sobrecargar `FotoEstado` con tablas temporales.

Preparación válida se reutiliza al confirmar, sin volver a consultar `/llaves` ni repetir verificación. Cambiar cripta/versión invalida preparación. Cancelar no instala un estado parcial. Un inicio fallido preserva cualquier partida previa hasta una confirmación válida. Preparación y resultado no se serializan en el guardado v4.

`--forzar` se transmite hasta cada ruta de nueva partida (consola y selección gráfica); nunca solo al parser. No añade un botón que omita errores ni permite convertir información incompleta en un diagnóstico binario. Cargar/replay siguen su semántica ya aprobada: no disparan una nueva verificación al construir internamente estado para restaurarlo/reproducirlo. Separar inicialización técnica de nueva partida para no bloquear registros de criptas iniciadas forzadamente.

## CLI — FR-RES-08/09/14/15

- `--verificar <cripta>` es un modo de solo verificación. Se despacha antes de crear/importar la vista y antes de preparar catálogo/estado; usa backend online u `--offline DIR`. Código0 resoluble,1 no resoluble,2 error de datos/consulta/presupuesto.
- `--verificar <cripta> --forzar`: solo verifica, no crea partida; el código sigue el resultado.
- `--verificar` junto con `--vista` o `--jugar`: prevalece solo verificación. Con `--replay`, `--cargar` o `--bench`: error de argumentos previo a HTTP/vista; `--cripta` duplicado debe coincidir o se rechaza.
- `--forzar` en una nueva partida permite el inicio imposible después de mostrar el reporte; no cambia código/resultado de `--verificar`. Nunca fuerza carga o respuesta corrupta.
- `--bench` existente incorpora sección003; no usa `/llaves` real, Pygame ni catálogo remoto.

## Interfaz — FR-RES-08/10/15

La selección solicita inicio a Sesión y recibe resultado incluso si no se creó partida. Presentar el reporte antes de entrar al juego; mantenerlo visible hasta continuar/volver. El forzado se configura con la bandera al lanzar y se refleja como advertencia explícita al continuar. Error incompleto vuelve a selección y muestra causa. La vista no interpreta reglas de puertas ni consulta C1.

Reutilizar tokens, paneles rectos, fuentes y scroll: cuerpo14–16 px, auxiliar≥11 px reales, interlineado múltiplo4, contraste≥4.5:1 normal y≥3:1 solo grande; no afirmar conformidad WCAG total. IDs largos y ciclo completo accesibles mediante envoltura/scroll, sin elipsis sin alternativa de foco/tooltip. Revisar menú/reporte, HUD, mapa e historial a640×480,1024×800 y1280×720, con nombres largos y errores. Capturas y comprobaciones se registran al implementar, no se afirman realizadas en este plan.

## Compatibilidad y aceptación del contrato

K1 amplía insumos y modelo con defaults compatibles; K5 añade preparación/reporte y forzado manteniendo inicio exitoso→FotoEstado. Guardado v4 y bitácora sin cambios. Falsos y offline deben cumplir `/llaves`; antiguas fixtures de nueva partida se actualizan o declaran error, sin bypass silencioso. Antes de integrar, aceptar propuesta, actualizar CONTRATOS.md y ejecutar pruebas001/002/004, cargas/replay y regresión de presupuesto. El servidor externo no forma parte del repositorio: este cambio define cliente, contrato y falsos; disponibilidad real es dependencia externa verificable.
