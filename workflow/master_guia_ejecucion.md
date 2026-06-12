# Guía Maestra de Ejecución y Flujo de Trabajo Basado en Agentes

Esta guía indexa el orden de ejecución sugerido para los agentes encargados de estructurar y maquetar el libro. Cada paso cuenta con un script `.py` de ejecución y su correspondiente archivo `.md` que contiene el prompt de evaluación (QA) y autorreparación que debe copiarse e interactuar con el agente en el futuro.

## Orden Recomendado de Copia y Pegado de Prompts

Para formatear, estandarizar y maquetar el libro completo, debes copiar y pegar los prompts de evaluación al agente en el siguiente orden secuencial:

### 1. Estandarización de Capítulos y Metadatos
*   **Script:** `workflow/01_metadatos.py`
*   **Prompt de Validación:** [prompt_01_metadatos.md](prompt_01_metadatos.md)
*   **Objetivo:** Configurar el YAML global (`_quarto.yml`), re-mapear autores y afiliaciones en el frontmatter, estandarizar bloques especiales (cajas, resúmenes, puntos clave, etc.) en Pandoc Divs y callouts oficiales de Quarto, aplicar numeración jerárquica manual in-place y limpiar la caché de compilación previa.

### 2. Vinculación de Bibliografía e Hipervínculos
*   **Script:** `workflow/02_bibliografia.py`
*   **Prompt de Validación:** [prompt_02_bibliografia.md](prompt_02_bibliografia.md)
*   **Objetivo:** Transformar referencias numéricas entre corchetes en el cuerpo del texto en hipervínculos internos, dar formato a la bibliografía final de cada capítulo envolviendo las referencias en un div con id único de ancla para el enlace, y verificar que no haya reprocesamientos duplicados (idempotencia).

### 3. Maquetación de Portada e Índice Responsivo
*   **Script:** `workflow/03_indice.py`
*   **Prompt de Validación:** [prompt_03_indice.md](prompt_03_indice.md)
*   **Objetivo:** Aplicar la grilla responsiva de tarjetas de capítulos en `index.qmd`, estandarizando alturas de imágenes, enlaces compactos y formato de autores. Finalmente, se encarga de eliminar automáticamente scripts antiguos obsoletos de la raíz.

---

## Cómo Funciona el Bucle de Autorreparación

Todos los prompts de validación contienen una directiva estricta para el agente:
> "Si la evaluación falla o falta algún criterio, NO me pidas permiso. Analiza el error, modifica el script .py para solucionarlo, restaura los archivos originales con git restore . y vuelve a intentarlo hasta que el output sea perfecto."

Esto garantiza que el agente no se detenga si algo falla. Evaluará los criterios de QA, si detecta alguna anomalía, revertirá los archivos modificados con Git, ajustará el código de los scripts de Python en la carpeta `workflow/` y re-ejecutará las validaciones automáticamente de forma iterativa hasta alcanzar la perfección.
