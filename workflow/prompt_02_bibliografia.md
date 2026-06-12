# Prompt de Evaluación - 02_bibliografia.py

## Contexto
El agente debe ejecutar el script para la vinculación y formateo de la bibliografía de todos los capítulos del libro:
```bash
python workflow/02_bibliografia.py
```
*(Nota: Para probar sin guardar cambios en disco, se puede pasar la bandera `--dry-run`)*

## Criterios de Evaluación (QA)
Tras la ejecución del script, el agente debe validar los siguientes puntos:
1. **Idempotencia**:
   - Comprobar que si el script ya fue ejecutado previamente en un archivo (se detecta la presencia del ancla `#ref-1` o `ref-1`), el archivo es omitido para evitar la duplicación o anidación incorrecta de enlaces.
2. **Hipervínculos en el Cuerpo del Texto**:
   - Las citas numéricas entre corchetes (ej: `[1]`, `[2, 3]`, `[1-3]`, `[1–3]`) deben haber sido transformadas en hipervínculos markdown que apunten al ancla `#ref-N` de la bibliografía final.
   - Ejemplo: `[1]` debe ser `[[1]](#ref-1)`.
   - Rangos de citas como `[1-3]` o `[1–3]` deben convertirse en enlaces separados vinculados y divididos por el guion correspondiente (ej. `[[1]](#ref-1)-[[3]](#ref-3)` o `[[1]](#ref-1)–[[3]](#ref-3)`).
3. **Sección de Bibliografía**:
   - Verificar que el inicio de la sección de bibliografía/referencias al final del capítulo se detectó correctamente, ya sea por encabezado formal (ej. `## Bibliografía`) o, en su defecto, mediante la contingencia de detección reversa desde el final del archivo.
   - Si se utilizó la contingencia por falta de encabezado formal, verificar que el script haya inyectado el encabezado `## Bibliografía` de manera automática justo antes de la lista bibliográfica.
4. **Formato de Entradas Bibliográficas**:
   - Cada entrada bibliográfica al final del capítulo debe estar numerada y envuelta en un elemento div con un ID único del tipo `ref-N` (ej: `<div id="ref-1">1. Texto de la referencia...</div>`).
   - Se debe mantener la limpieza removiendo numeraciones previas o viñetas que existían de forma manual al inicio de cada entrada.
   - Las líneas de número de página final o subtítulos cortos en la bibliografía deben ser respetados sin envolver en divs con IDs de referencia.

## Bucle de Autorreparación
Si la evaluación falla o falta algún criterio, NO me pidas permiso. Analiza el error, modifica el script `workflow/02_bibliografia.py` para solucionarlo, restaura los archivos originales con `git restore .` y vuelve a intentarlo hasta que el output sea perfecto.
