# Prompt de Evaluación - 01_metadatos.py

## Contexto
El agente debe ejecutar el script de metadatos y estandarización de capítulos:
```bash
python workflow/01_metadatos.py
```

## Criterios de Evaluación (QA)
Tras la ejecución del script, el agente debe validar los siguientes puntos:
1. **Archivo `_quarto.yml`**:
   - Debe contener `lang: es` al inicio de la raíz.
   - Debe tener configurado `number-sections: false` dentro de la sección de formato HTML para evitar numeraciones automáticas redundantes.
2. **Metadatos en Capítulos (`01-capitulo-*.qmd` a `14-capitulo-*.qmd`)**:
   - El frontmatter YAML de cada capítulo debe mapear la clave `author:` de forma estructurada con `name`, `orcid` y `affiliation`.
   - Las afiliaciones y nombres de autor deben coincidir con la fuente de verdad en `prelim-lista-de-autores.qmd`, usando superíndices (ej. `^1^` en nombre y `^1^Institución` en affiliation).
   - El frontmatter YAML debe contener al final las claves de compilación obligatorias `date: ""` y `doi: ""`.
3. **Cuerpo del Texto**:
   - Cualquier bloque de afiliación de texto plano que estuviese al inicio del cuerpo del capítulo debe haber sido removido.
   - Las secciones `## Resumen {.unnumbered}` y `## Abstract {.unnumbered}` deben estar envueltas correctamente en divs Pandoc: `::: {#resumen}` y `::: {#abstract}`.
   - Los bloques de información con la clase antigua `::: {.caja-box}` deben ser transformados en callouts estilizados oficiales de Quarto: `::: {#boxX .callout-important ...}` con fondo azul claro (`#e3f0fbff`), padding de `20px` y `border: none !important;` y sin encabezados separados. La frase inicial del contenido (e.g. `**Caja X.**`) debe estar en negrita.
   - Las tablas con Puntos Clave, Recomendaciones, Retos y Trabajo a Futuro deben haber sido convertidas a sus respectivos callouts estilizados con color de fondo inline específico, padding de `20px`, sin bordes (`border: none !important;`), y con su frase inicial en negrita.
4. **Numeración In-Place**:
   - Los encabezados `##` (H2) y `###` (H3) deben estar numerados manualmente en el texto siguiendo la jerarquía `{Capítulo}.{H2}` y `{Capítulo}.{H2}.{H3}` (ej: `## 3.1 Introducción` y `### 3.1.1 Antecedentes`).
   - Se deben ignorar y no numerar las secciones de Resumen, Abstract y Bibliografía.
5. **Limpieza**:
   - Las carpetas temporales de caché de compilación (`_book/` y `.quarto/`) deben haber sido completamente eliminadas.

## Bucle de Autorreparación
Si la evaluación falla o falta algún criterio, NO me pidas permiso. Analiza el error, modifica el script `workflow/01_metadatos.py` para solucionarlo, restaura los archivos originales con `git restore .` y vuelve a intentarlo hasta que el output sea perfecto.
