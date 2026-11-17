# Reglas del proyecto

## Cambios de interfaz

- Leer y aplicar [docs/diseno-ui.md](docs/diseno-ui.md) antes de modificar `src/view/`.
- Mantener la estética del juego: esquinas rectas, paleta compartida, retícula de4/8 px, sprites existentes y controles coherentes. No introducir radios de borde.
- Usar los roles tipográficos compartidos: base16 px, texto continuo14–16 px, auxiliar≥11 px reales, pesos400/500/600 y700 solo en títulos grandes/alertas. No reducir texto por debajo del mínimo para hacer que quepa: ajustar distribución, envolver o desplazar.
- Conservar cifras tabulares en relojes, vida y contadores; interlineados finales en múltiplos de4 px. No aplicar Bold a todo ni simular pesos finos.
- Verificar contraste de cada pareja texto/fondo:≥4.5:1 para texto normal y≥3:1 solo para texto grande. No afirmar conformidad WCAG completa solo por pasar esa comprobación.
- Truncar con elipsis solo si hay acceso al texto completo mediante tooltip y alternativa de foco/selección. Ajustar el tooltip a la ventana.
- Reutilizar tokens/componentes de la interfaz; revisar capturas de menús, HUD, mapa e historial a640×480,1024×800 y formato panorámico, con nombres largos y errores.
- La vista consume Sesión/DTO; no introduce reglas del motor ni llamadas a C1/API. Registrar cambios y validación en DECISIONES.md/PROMPTS_LLM.md. Hacer commits por hitos cuando esté autorizado.
