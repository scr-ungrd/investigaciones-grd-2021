# Prompt de Evaluación - 03_indice.py

## Contexto
El agente debe ejecutar el script para el procesamiento del índice y la portada del libro:
```bash
python workflow/03_indice.py
```

## Criterios de Evaluación (QA)
Tras la ejecución del script, el agente debe validar los siguientes puntos:
1. **Grilla Responsiva**:
   - Comprobar que en `index.qmd` se inyecta correctamente el contenedor general de la grilla: `::: {.grid .indice-grid}`.
   - Cada tarjeta de capítulo debe estar envuelta en las clases responsivas: `::: {.g-col-12 .g-col-md-6}`.
2. **Estructura y Estilos de las Tarjetas**:
   - Cada tarjeta debe tener el formato `::: {.card .h-100 .shadow-sm}`.
   - El encabezado de la tarjeta (`.card-header .pt-2 .pb-2`) debe contener el título del capítulo como enlace con formato compacto: `[Título del Capítulo](ruta_capitulo.html){.fs-6 .fw-bold .text-decoration-none}`.
   - La imagen del capítulo en el cuerpo de la tarjeta (`.card-body .pt-2 .pb-2`) debe tener atributos de altura y estilo inline para asegurar uniformidad: `![](ruta_imagen){height="130px" style="object-fit: cover;"}`.
   - Los autores del capítulo en el cuerpo de la tarjeta deben estar envueltos en un párrafo con clase específica: `<p class="autores-text">**Autores:** Nombres...</p>`.
3. **Sintaxis de Bloques Pandoc**:
   - Se debe verificar que existen saltos de línea (líneas vacías) adecuados alrededor de cada apertura/cierre de bloques `:::` para evitar problemas en el procesamiento de Pandoc.
4. **Limpieza de Scripts Obsoletos**:
   - Verificar que los scripts antiguos de indexación `embellecer_indice.py` y `reparar_indice.py` ya no existen en la raíz del proyecto (deben haber sido eliminados por el script).

## Bucle de Autorreparación
Si la evaluación falla o falta algún criterio, NO me pidas permiso. Analiza el error, modifica el script `workflow/03_indice.py` para solucionarlo, restaura los archivos originales con `git restore .` y vuelve a intentarlo hasta que el output sea perfecto.
