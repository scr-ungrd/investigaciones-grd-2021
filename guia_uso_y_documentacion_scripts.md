# Guía de Uso y Documentación de Scripts de Estilos y Migración (UNGRD)

Este documento detalla el funcionamiento, las modificaciones realizadas y el manual de uso para los scripts desarrollados para la estandarización arquitectónica y de estilos del libro **"Investigaciones en Gestión del Riesgo de Desastres para Colombia del 2021"**.

---

## Arquitectura General de Procesamiento

El flujo de trabajo automatizado toma los contenidos crudos de Quarto Markdown (`.qmd`) y los transforma en páginas estructuradas que interactúan con las reglas de estilo definidas en `custom.css` y `custom.scss`.

```mermaid
graph TD
    A[prelim-lista-de-autores.qmd] -->|Fuente de Verdad de Autores| B(herramienta_migracion_ungrd.py)
    C[capitulos 01-14 .qmd crudos] --> B
    D[_quarto.yml original] --> B
    
    B -->|Genera/Modifica| E[capitulos 01-14 .qmd estandarizados]
    B -->|Modifica| F[_quarto.yml config]
    B -->|Elimina Caché| G[_book/ y .quarto/]
    
    H[index.qmd crudo/procesado] --> I(procesar_indice_ungrd.py)
    I -->|Genera Cuadrícula de Tarjetas| J[index.qmd beautified]
    I -->|Elimina Temporales| K[Scripts obsoletos]
    
    E & J -->|Compilación con Quarto| L[Libro HTML Renderizado]
    M[custom.css / custom.scss] -->|Aplica Estilos Visuales| L
```

---

## 1. `herramienta_migracion_ungrd.py`
**Propósito:** Es el script maestro de migración y consolidación arquitectónica. Se encarga de procesar los capítulos individuales del libro en una sola pasada para aplicar el estándar oficial de metadatos, cajas, resúmenes y numeración manual.

### Archivos que Modifica
*   `_quarto.yml` (Configuración global del libro)
*   `01-capitulo-*.qmd` hasta `14-capitulo-*.qmd` (Archivos de capítulos individuales)
*   Elimina carpetas temporales de caché: `_book/` y `.quarto/`

### Detalles Técnicos de las Modificaciones

#### A. Configuración Global (`_quarto.yml`)
*   **Idioma:** Inserta `lang: es` al inicio de la raíz si no está presente.
*   **Numeración Nativa de Quarto:** Reemplaza `number-sections: true` por `number-sections: false` o lo inyecta bajo el formato HTML. Esto se hace porque el script implementa una numeración manual in-place, evitando colisiones con la numeración automática de Quarto.

#### B. Metadatos de Autores y Afiliaciones (Frontmatter YAML)
*   **Fuente de Verdad:** Lee `prelim-lista-de-autores.qmd` y mapea los autores por nombre para obtener sus afiliaciones oficiales.
*   **Estructura del YAML:** Convierte las listas de autores simples en bloques estructurados que respetan el orden exacto y relacionan los autores con sus afiliaciones mediante superíndices (e.g., `^1^`, `^1,2^`).
    ```yaml
    author:
      - name: "Nombre Autor ^1,2^"
        orcid: ""
        affiliation: "^1^Institución A; ^2^Institución B"
    ```
*   **Limpieza de Cuerpo:** Elimina cualquier texto plano de afiliaciones que pudiera estar al inicio del cuerpo del capítulo.
*   **Campos Requeridos:** Inyecta las llaves vacías `date: ""` y `doi: ""` requeridas para la compilación correcta en el formato de libro.

#### C. Bloques Especiales (Resumen, Abstract y Cajas)
*   **Resumen y Abstract:** Envuelve las secciones `## Resumen {.unnumbered}` y `## Abstract {.unnumbered}` en bloques contenedores Pandoc Divs (`::: {#resumen}` y `::: {#abstract}`). Esto permite que el archivo CSS aplique los colores de fondo de forma precisa:
    *   **Resumen:** Fondo azul claro (`#eff6ff`) y borde azul (`#bfdbfe`).
    *   **Abstract:** Fondo amarillo claro (`#FDF6D9`) y borde dorado (`#E8D995`).
*   **Cajas de Información (.caja-box):** Transforma la sintaxis obsoleta `::: {.caja-box}` a callouts estilizados oficiales de Quarto (`::: {#boxX .callout-important ...}`) con colores institucionales inline y sin bordes:
    *   **Fondo:** Azul claro (`#e3f0fbff`), padding de `10px` y `border: none !important;` (sin bordes).
    *   **Formato de Texto:** No genera títulos ni encabezados separados, ya que las cajas no tienen títulos. En su lugar, el contenido de la caja se inyecta directamente dentro del callout, destacando en negrita únicamente el identificador inicial `**Caja X.**` al principio del párrafo.
*   **Puntos Clave:** Transforma las tablas de puntos clave (`| PUNTOS CLAVE ... |` y su separador `| --- |`) en callouts estilizados sin bordes:
    *   **Fondo:** Lila muy claro (`#f4ebffff`), padding de `10px` y `border: none !important;`.
    *   **Formato de Texto:** Inserta el texto directamente dentro del callout, destacando en negrita únicamente el identificador inicial `**Puntos clave.**`.
*   **Recomendaciones para Tomar Decisiones:** Transforma las tablas de recomendaciones (`| RECOMENDACIÓNES PARA TOMAR DECISIONES ... |` y su separador `| --- |`) en callouts estilizados sin bordes:
    *   **Fondo:** Rosa muy claro (`#fff0f3ff`), padding de `10px` y `border: none !important;`.
    *   **Formato de Texto:** Inserta el texto directamente dentro del callout, destacando en negrita únicamente el identificador inicial `**Recomendaciones para tomar decisiones.**`.
*   **Retos:** Transforma las tablas de retos (`| RETOS ... |` y su separador `| --- |`) en callouts estilizados sin bordes:
    *   **Fondo:** Verde muy claro (`#eafaf1ff`), padding de `10px` y `border: none !important;`.
    *   **Formato de Texto:** Inserta el texto directamente dentro del callout, destacando en negrita únicamente el identificador inicial `**Retos.**`.
*   **Trabajo a Futuro:** Transforma las tablas de trabajo a futuro (`| TRABAJO FUTURO ... |` o `| TRABAJO A FUTURO ... |` y su separador `| --- |`) en callouts estilizados sin bordes:
    *   **Fondo:** Amarillo claro (`#fffbebff`), padding de `10px` y `border: none !important;`.
    *   **Formato de Texto:** Inserta el texto directamente dentro del callout, destacando en negrita únicamente el identificador inicial `**Trabajo a futuro.**`.

#### D. Numeración In-Place (Jerárquica)
*   Extrae el número de capítulo del nombre del archivo (e.g., `03-capitulo-3...` -> `3`).
*   Analiza los encabezados de segundo y tercer nivel en el cuerpo del capítulo (ignorando Resumen y Abstract) y les asigna manual in-place:
    *   `## Título` $\rightarrow$ `## {Capítulo}.{Secuencia_H2} Título` (ej. `## 3.1 Introducción`)
    *   `### Subtítulo` $\rightarrow$ `### {Capítulo}.{Secuencia_H2}.{Secuencia_H3} Subtítulo` (ej. `### 3.1.1 Antecedentes`)

### Guía de Uso
1.  Asegúrate de estar en la raíz del repositorio.
2.  Ejecuta el script usando Python 3:
    ```bash
    python3 herramienta_migracion_ungrd.py
    ```
3.  **Resultado esperado:** El script imprimirá en consola el progreso de configuración de `_quarto.yml`, la carga de autores, el procesamiento de cada uno de los 14 capítulos y finalmente la purga de caché.

---

## 2. `procesar_indice_ungrd.py`
**Propósito:** Procesa y formatea el archivo `index.qmd` (Portada e Inicio del libro) para aplicar una maquetación moderna con una rejilla responsiva (grid) de Bootstrap y tarjetas homogéneas para cada capítulo.

### Archivos que Modifica
*   `index.qmd` (Página de inicio/portada)
*   Elimina scripts de maquetación antiguos y obsoletos si existen en la raíz: `embellecer_indice.py` y `reparar_indice.py`.

### Detalles Técnicos de las Modificaciones
*   **Detección de Estado:** Evalúa si `index.qmd` ya está procesado buscando la clase `.indice-grid`. Si está en estado "crudo", migra la estructura básica a una rejilla CSS moderna.
*   **Estructura de la Rejilla:** Envuelve el listado de capítulos en una grilla responsiva de dos columnas para pantallas medianas y grandes (`.g-col-md-6`):
    ```markdown
    ::: {.grid .indice-grid}
    ::: {.g-col-12 .g-col-md-6}
    ::: {.card .h-100 .shadow-sm}
      ::: {.card-header .pt-2 .pb-2}
         [Enlace al Capítulo](link.html){.fs-6 .fw-bold .text-decoration-none}
      :::
      ::: {.card-body .pt-2 .pb-2}
         ![](ruta_imagen_miniatura){height="130px" style="object-fit: cover;"}
         <p class="autores-text">**Autores:** Nombres de autores</p>
      :::
    :::
    :::
    :::
    ```
*   **Estandarización de Títulos:** Reescribe el enlace de los títulos dentro de `.card-header` inyectando las clases de Bootstrap `.fs-6` (tamaño de fuente compacto para evitar saltos de línea innecesarios), `.fw-bold` (negrita) y `.text-decoration-none` (remueve el subrayado por defecto), logrando que la tarjeta mantenga una altura uniforme.
*   **Ajuste de Altura de Imagen:** Fuerza que la etiqueta de la imagen incluya atributos inline para limitar su altura vertical a `130px` y aplicar `object-fit: cover` (ej. `{height="130px" style="object-fit: cover;"}`), compactando de manera drástica la altura de las tarjetas.
*   **Ajuste de Padding:** Añade clases de padding reducido (`.pt-2 .pb-2`) tanto al `card-header` como al `card-body` para estrechar la separación vertical entre los elementos internos de la tarjeta.
*   **Estandarización de Autores:** Envuelve la línea de autores en un párrafo con la clase `.autores-text` para forzar un diseño más sutil (tamaño de fuente `0.85rem` y color `#6b7280`).

### Guía de Uso
1.  Ejecuta el script desde la raíz del proyecto:
    ```bash
    python3 procesar_indice_ungrd.py
    ```
2.  **Resultado esperado:** Actualización de `index.qmd` con la sintaxis de tarjetas de grilla responsiva (2 por fila en escritorio), imágenes de `130px` de altura, enlaces estilizados con `.fs-6` y padding reducido.


---

## 3. `vincular_bibliografia.py`
**Propósito:** Este script automatiza la conversión de citas académicas en texto plano a hipervínculos internos HTML en documentos Quarto (`.qmd`), soportando citas individuales, listas y rangos de citas (ej. `[1-3]`, `[1, 2, 5]`, o `[1–3]`), además de generar los identificadores y anclas HTML en la bibliografía final de cada capítulo.

### Archivos que Modifica
*   `01-capitulo-*.qmd` hasta `14-capitulo-*.qmd` (Archivos de capítulos individuales)

### Detalles Técnicos de las Modificaciones

#### A. Conversión de Citas en el Cuerpo del Texto
El script localiza cadenas numéricas entre corchetes mediante expresiones regulares (ej. `[1]`, `[2, 3]`, `[1-3]`) y reemplaza cada número con un enlace dinámico hacia el ancla de la bibliografía correspondiente (ej. `[[1]](#ref-1)`). Soporta:
*   **Listas de citas:** Separadas por comas.
*   **Rangos de citas:** Utilizando guiones cortos `-` y rayas o guiones largos `–` (ej. `[1-3]` se convierte en enlaces individuales vinculados y separados por el guion).

#### B. Heurística de Búsqueda de la Bibliografía
El script utiliza una heurística robusta de dos niveles para localizar el inicio de la bibliografía:
1.  **Detección por Encabezado Formal:** Escanea las líneas del archivo buscando coincidencias exactas con palabras clave de bibliografía (`BIBLIOGRAFÍA`, `REFERENCIAS` o `LITERATURA`, sin importar mayúsculas/minúsculas y delimitadas por límites de palabra `\b`), validando que empiece con caracteres de encabezado como `#`, `**` o dígitos.
2.  **Plan de Contingencia (Detección sin título / Sección de Autores):** En caso de no encontrar ningún encabezado formal (por ejemplo, si las referencias siguen directamente a la sección de autores del capítulo o no hay título de referencias), el script realiza una búsqueda reversa (desde el final hacia arriba) de la primera línea que comience con un patrón de lista bibliográfica como `[1] ` o `1. `. Al detectarla, asume que ese es el inicio de la bibliografía e inyecta un encabezado estándar `## Bibliografía` de forma automática.

#### C. Idempotencia y Procesamiento Seguro
Para evitar el reprocesamiento accidental o la duplicación de enlaces en ejecuciones subsecuentes, el script incluye un control de **idempotencia**. Antes de procesar cualquier archivo, realiza una inspección rápida del contenido: si detecta la cadena `#ref-1` o `ref-1`, omitirá el archivo imprimiendo en consola que ya ha sido procesado previamente.

### Guía de Uso y Comando en Lote
Para ejecutar el procesamiento de forma segura sobre todos los capítulos (`01-14`) de forma automatizada (en lote), el script cuenta con un modo de simulación (`--dry-run`):

*   **Ejecución Segura de Simulación (Dry-Run):** Permite verificar qué capítulos contienen la bibliografía y qué estrategia se utilizará sin modificar los archivos físicos.
    ```bash
    python3 vincular_bibliografia.py --dry-run
    ```
*   **Ejecución de Aplicación en Lote (En el lugar / In-place):** Aplica la vinculación y reescritura de los archivos de forma definitiva.
    ```bash
    python3 vincular_bibliografia.py
    ```

---

## 4. `scratch/fix_chapters.py` (Script de Corrección Temporal)
**Propósito:** Es un script de utilidad temprana ubicado en la carpeta `scratch/` que realiza tareas de formateo rápido en los archivos `.qmd` antes de aplicar la migración arquitectónica principal.

### Archivos que Modifica
*   Todos los archivos `.qmd` ubicados en el directorio del proyecto.

### Detalles Técnicos de las Modificaciones
1.  **Color del Banner:** Modifica o inyecta la propiedad `title-block-banner-color: "#151550ff"` (azul oscuro institucional) en el frontmatter YAML de los capítulos.
2.  **Conversión de Encabezados:** Convierte textos en negrita como `**Resumen**` y `**Abstract**` a encabezados formales no numerados de nivel 2: `## Resumen {.unnumbered}` y `## Abstract {.unnumbered}`.
3.  **Unificación de Palabras Clave:** Busca variaciones de "Key words", "Keywords", "Keywords  " o "Key words  " y las reemplaza uniformemente por la versión en negrita estándar: `**Keywords**`.

### Guía de Uso
> [!NOTE]
> Este script contiene una ruta absoluta estática hacia el directorio `/home/nia/scr-ungrd/investigaciones-grd-2021` en la línea 4. Si deseas utilizarlo en tu entorno de trabajo actual, debes editar esa línea o ejecutar los scripts maestros principales (`herramienta_migracion_ungrd.py` y `procesar_indice_ungrd.py`), los cuales ya incluyen y superan estas correcciones de forma segura e independiente de rutas absolutas locales.

Comando de ejecución:
```bash
python3 scratch/fix_chapters.py
```

---

## Relación con el Sistema de Estilos (`custom.css` y `custom.scss`)

Los scripts no trabajan aislados, sino que estructuran el código HTML/Markdown generado por Quarto para que coincida exactamente con las reglas definidas en las hojas de estilo:

| Elemento Modificado | Selector CSS Relacionado | Estilo Aplicado por la Hoja de Estilo |
| :--- | :--- | :--- |
| Contenedores `::: {#resumen}` | `#resumen` / `#resumen h1` | Aplica fondo azul suave `#eff6ff`, bordes limpios y título en color azul `#3b82f6`. |
| Contenedores `::: {#abstract}` | `#abstract` / `#abstract h1` | Aplica fondo crema suave `#FDF6D9`, bordes limpios y título en color dorado/ocre `#B8860B`. |
| Bloques de Tarjetas en Índice | `.indice-grid .card` | Agrega una sombra sutil, bordes redondeados de `10px`, y un efecto interactivo `hover` con desplazamiento vertical (`translateY(-5px)`) y sombra extendida. |
| Miniaturas de Capítulos | `.indice-grid .card-body img` | Estandariza el tamaño de todas las imágenes de portada en el índice a una altura fija de `190px` con recorte inteligente (`object-fit: cover`) y borde suave. |
| Enlaces en Tarjetas | `.indice-grid .card-header a` | Cambia el color de los enlaces a azul oscuro institucional (`#151550`) y aplica cambio de color a `#2c7bb6` al pasar el mouse. |
| Bloques de Caja (`#box1`, etc.) | `#box1`, `#box2`, `#caja1` | Fuerza la tipografía Arial (requisito editorial), remueve bordes (`border: none !important;`) y reduce los márgenes/paddings internos para mantener compactas las cajas. |
| Bloques de Puntos Clave (`#puntos-clave-1`, etc.) | `#puntos-clave-X` | Aplica fondo lila muy claro `#f4ebffff`, padding interno de `10px` y remueve bordes (`border: none !important;`). |
| Bloques de Recomendaciones (`#recomendaciones-1`, etc.) | `#recomendaciones-X` | Aplica fondo rosa muy claro `#fff0f3ff`, padding interno de `10px` y remueve bordes (`border: none !important;`). |
| Bloques de Retos (`#retos-1`, etc.) | `#retos-X` | Aplica fondo verde muy claro `#eafaf1ff`, padding interno de `10px` y remueve bordes (`border: none !important;`). |
| Bloques de Trabajo a Futuro (`#trabajo-futuro-1`, etc.) | `#trabajo-futuro-X` | Aplica fondo amarillo claro `#fffbebff`, padding interno of `10px` y remueve bordes (`border: none !important;`). |
| Tablas de Datos (Primera fila) | `th`, `table > thead > tr > th` | Aplica fondo gris claro `#f0f0f0 !important;` y texto en negrita a la cabecera de las columnas en todas las tablas. |


---

## Recomendaciones para el Flujo de Trabajo

Si realizas cambios en el contenido o deseas reiniciar el formateo del libro:
1.  **Modificar contenidos crudos:** Realiza los cambios que requieras sobre los archivos `.qmd`.
2.  **Ejecutar herramientas en orden:**
    *   Primero corre la consolidación de capítulos: `python3 herramienta_migracion_ungrd.py`
    *   Luego corre la consolidación del índice: `python3 procesar_indice_ungrd.py`
3.  **Verificar y Compilar:** Puedes compilar localmente con Quarto para previsualizar los cambios usando:
    ```bash
    quarto render
    ```
    *(Nota: La integración continua de GitHub Actions compilará y publicará de manera automática en la rama `gh-pages` cada vez que hagas un push a `main`).*
