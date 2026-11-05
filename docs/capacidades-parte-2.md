# Capacidades de la parte 2

Las especificaciones se mantienen en `specs/`, una carpeta por capacidad,
con el formato de GitHub Spec Kit. Este índice sustituye las descripciones
agrupadas anteriores; los textos de entrada se conservan en cada `spec.md`.

| Capacidad | Especificación | Requisitos |
| --- | --- | --- |
| Terreno y cazador | [001-terreno-cazador](../specs/001-terreno-cazador/spec.md) | FR-CAZ |
| Niebla de guerra e «ir a» | [002-niebla-ir-a](../specs/002-niebla-ir-a/spec.md) | FR-NIE |
| Verificación de resolubilidad | [003-resolubilidad](../specs/003-resolubilidad/spec.md) | FR-RES |
| Línea de tiempo | [004-linea-de-tiempo](../specs/004-linea-de-tiempo/spec.md) | FR-LIN |

Cada carpeta incluye `checklists/requirements.md` para revisar la calidad de
la especificación. Los documentos están en borrador; los supuestos explícitos
se revisan con `$speckit-clarify` antes de planificar.

Después de revisar, hacer commit de cada especificación antes de crear su
`plan.md`, `tasks.md` o código. Las mediciones y decisiones se documentarán
al implementar, sin presentar objetivos de rendimiento como resultados medidos.

## Continuar con Spec Kit

La integración local guarda la capacidad activa en `.specify/feature.json`
(estado local excluido de Git). Al terminar este ajuste queda activa
`specs/004-linea-de-tiempo`.

Para trabajar en otra capacidad, establecer `SPECIFY_FEATURE_DIRECTORY` con
su ruta al invocar las habilidades; por ejemplo, indicar en el mensaje:

```text
$speckit-clarify
SPECIFY_FEATURE_DIRECTORY=specs/001-terreno-cazador
```

Las rutas son independientes de la rama Git. La configuración y las plantillas
permanecen en `.specify/`; las especificaciones del proyecto, en `specs/`.
