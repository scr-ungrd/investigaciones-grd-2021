#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Maestro de Migración y Consolidación Arquitectónica - UNGRD
-----------------------------------------------------------------
Este script realiza la migración completa de un libro "crudo" en una sola pasada:
1. Metadatos y YAML:
   - Lee 'prelim-lista-de-autores.qmd' como fuente de verdad.
   - Re-mapea el frontmatter YAML de los capítulos '.qmd' estructurando 'author:'
     (con name conteniendo los superíndices, orcid vacío y affiliation conteniendo
      el superíndice seguido del texto institucional completo de la fuente de verdad).
   - Inyecta 'date: ""' y 'doi: ""' en cada capítulo.
   - Configura 'lang: es' y 'number-sections: false' en '_quarto.yml'.
2. Cajas y Resúmenes:
   - Envuelve '## Resumen {.unnumbered}' y '## Abstract {.unnumbered}' en Pandoc divs.
   - Transforma los bloques '::: {.caja-box}' a callouts estilizados UNGRD con títulos <h2>.
3. Numeración In-Place:
   - Extrae el número de capítulo del nombre del archivo.
   - Aplica numeración jerárquica manual '## {cap}.{h2}' y '### {cap}.{h2}.{h3}'
     in-place (ignorando Resumen y Abstract).
4. Limpieza Interna:
   - Elimina las carpetas temporales '_book/' y '.quarto/' al finalizar.
"""

import os
import re
import glob
import shutil
import unicodedata
import subprocess

# Ruta raíz del proyecto (un nivel arriba del script en workflow/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def normalize_string(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    return s.strip().lower()

def clean_for_comparison(s):
    s = normalize_string(s)
    return "".join([c for c in s if c.isalnum()])

def get_matching_master_affiliation(chapter_aff, master_aff_full):
    if not chapter_aff or not master_aff_full:
        return None
    chapter_clean = clean_for_comparison(chapter_aff)
    master_parts = [p.strip() for p in master_aff_full.split(".") if p.strip()]
    matched_parts = []
    for part in master_parts:
        part_clean = clean_for_comparison(part)
        if len(part_clean) < 8:
            continue
        if part_clean in chapter_clean or chapter_clean in part_clean:
            matched_parts.append(part)
        else:
            min_len = min(len(chapter_clean), len(part_clean))
            compare_len = min(min_len, 20)
            if compare_len >= 10 and chapter_clean[:compare_len] == part_clean[:compare_len]:
                matched_parts.append(part)
    if matched_parts:
        return ". ".join(matched_parts)
    return None

def load_master_authors():
    author_map = {}
    master_file = os.path.join(PROJECT_ROOT, "prelim-lista-de-autores.qmd")
    if not os.path.exists(master_file):
        print(f"[Error] No se encontró la fuente de verdad: {master_file}")
        return author_map
        
    with open(master_file, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                parts = line.split("|", 1)
                name = parts[0].replace("*", "").strip()
                aff = parts[1].replace("*", "").strip()
                author_map[normalize_string(name)] = aff
    print(f"[Metadatos] Cargados {len(author_map)} autores desde la fuente de verdad.")
    return author_map

def parse_current_authors(yaml_text):
    authors = []
    lines = yaml_text.splitlines()
    current_author = None
    
    for line in lines:
        name_match = re.match(r'^\s+-\s*name:\s*"([^"]+)"', line)
        if name_match:
            if current_author:
                authors.append(current_author)
            current_author = {"name": name_match.group(1), "orcid": "", "affiliation": ""}
            continue
            
        if current_author:
            orcid_match = re.match(r'^\s+orcid:\s*"([^"]*)"', line)
            if orcid_match:
                current_author["orcid"] = orcid_match.group(1)
                continue
            aff_match = re.match(r'^\s+affiliation:\s*"([^"]*)"', line)
            if aff_match:
                current_author["affiliation"] = aff_match.group(1)
                continue
                
        if line.strip() and not line.startswith(" ") and not line.startswith("-"):
            if current_author:
                authors.append(current_author)
                current_author = None
                
    if current_author:
        authors.append(current_author)
        
    return authors

def extract_original_affiliations(fpath, current_yaml, current_body):
    affiliations = {}
    
    # 1. Intentar extraer del cuerpo del archivo (si es una corrida sobre el crudo)
    heading_match = re.search(r'^#+\s+', current_body, re.MULTILINE)
    if heading_match:
        pre_heading = current_body[:heading_match.start()]
        lines = [l.strip() for l in pre_heading.splitlines() if l.strip()]
        
        has_affiliations = False
        aff_lines = []
        for l in lines:
            if ":::" in l:
                continue
            if re.search(r'Autor de contacto|Correo-e', l, re.IGNORECASE):
                continue
            if re.search(r'\*\*[^*]+\*\*', l):
                continue
            # Buscamos que empiece con dígito o contenga palabras clave de afiliación
            if re.match(r'^\d+\s*\w+', l) or any(k in l.lower() for k in ["universidad", "departamento", "instituto", "centro", "consultoría", "escuela", "servicio", "facultad", "fundación", "asociación"]):
                aff_lines.append(l)
                has_affiliations = True
                
        if has_affiliations:
            for idx, line in enumerate(aff_lines):
                m = re.match(r'^(\d+)\s*(.*)$', line)
                if m:
                    num = m.group(1)
                    text = m.group(2).strip()
                    affiliations[num] = text
                else:
                    num = str(idx + 1)
                    affiliations[num] = line.strip()

    # 2. Fallback 1: Recuperar versión de git (si ya fue procesado pero está bajo control de versiones)
    if not affiliations:
        try:
            rel_fpath = os.path.relpath(fpath, PROJECT_ROOT)
            result = subprocess.run(["git", "show", f"HEAD:{rel_fpath}"], capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT)
            if result.returncode == 0:
                orig_content = result.stdout
                yaml_match = re.match(r'^---\n(.*?)\n---\s*\n(.*)', orig_content, re.DOTALL)
                if yaml_match:
                    orig_body = yaml_match.group(2)
                    orig_heading = re.search(r'^#+\s+', orig_body, re.MULTILINE)
                    if orig_heading:
                        orig_pre = orig_body[:orig_heading.start()]
                        orig_lines = [l.strip() for l in orig_pre.splitlines() if l.strip()]
                        orig_aff_lines = []
                        for l in orig_lines:
                            if ":::" in l:
                                continue
                            if re.search(r'Autor de contacto|Correo-e', l, re.IGNORECASE):
                                continue
                            if re.search(r'\*\*[^*]+\*\*', l):
                                continue
                            if re.match(r'^\d+\s*\w+', l) or any(k in l.lower() for k in ["universidad", "departamento", "instituto", "centro", "consultoría", "escuela", "servicio", "facultad", "fundación", "asociación"]):
                                orig_aff_lines.append(l)
                        for idx, line in enumerate(orig_aff_lines):
                            m = re.match(r'^(\d+)\s*(.*)$', line)
                            if m:
                                num = m.group(1)
                                text = m.group(2).strip()
                                affiliations[num] = text
                            else:
                                num = str(idx + 1)
                                affiliations[num] = line.strip()
        except Exception:
            pass

    # 3. Fallback 2: Parsear desde el YAML actual (si ya está estructurado)
    if not affiliations:
        current_authors = parse_current_authors(current_yaml)
        for aut in current_authors:
            aff_val = aut.get("affiliation", "")
            if aff_val:
                parts = [p.strip() for p in aff_val.split(";") if p.strip()]
                for part in parts:
                    m = re.match(r'^\^([^^]+)\^(.*)$', part)
                    if m:
                        num = m.group(1)
                        text = m.group(2).strip()
                        affiliations[num] = text

    return affiliations

def split_title_body(text):
    text = text.strip()
    double_space_match = re.search(r'\s{2,}', text)
    if double_space_match:
        split_idx = double_space_match.start()
        title = text[:split_idx].strip()
        body = text[split_idx:].strip()
        if title and body:
            return title, body

    m = re.search(r'([\?!:]+)\s+([A-Z“"1-9])', text)
    if m:
        split_idx = m.end(1)
        title = text[:split_idx].strip()
        body = text[split_idx:].strip()
        return title, body

    for m in re.finditer(r'\.\s+([A-Z“"1-9])', text):
        idx = m.start()
        prefix = text[:idx]
        abbrev_pattern = r'(et\s+al|p\.?\s*ej|cop\$|no|d\.?\s*c)$'
        if not re.search(abbrev_pattern, prefix, re.IGNORECASE):
            title = text[:idx+1].strip()
            body = text[idx+1:].strip()
            return title, body

    body_start_words = {
        "los", "el", "la", "este", "como", "en", "un", "de", "las", "aunque", 
        "vale", "existe", "según", "anfibios", "sustrato", "cambio", "claridad", 
        "procesos", "conocimiento", "estudios", "formas", "caracterización", 
        "identificación", "acciones", "bienestar", "directriz", "condiciones", 
        "especies", "seguridad", "zoonosis", "sistema", "one", "marco", 
        "conceptos", "definitions", "drought", "teoría", "datos", "cuenca", 
        "causas", "medidas", "retos", "modelo", "beidou", "coherencia", 
        "gifreu", "inundaciones", "cuantitativamente", "antecedentes", "r-crisis"
    }
    
    words = text.split()
    if len(words) > 1:
        for i in range(1, len(words)):
            word = words[i]
            clean_word = re.sub(r'^[“"\[\(]+', '', word)
            clean_word = re.sub(r'[.,;:!?\]\)]+$', '', clean_word)
            if not clean_word:
                continue
            first_word_clean = re.sub(r'[.,;:!?\]\)]+$', '', words[0]).lower()
            if (clean_word.lower() in body_start_words and clean_word[0].isupper()) or \
               (clean_word.lower() == first_word_clean and i > 0):
                split_pattern = r'\s+' + re.escape(word)
                match = re.search(split_pattern, text)
                if match:
                    split_idx = match.start()
                    title = text[:split_idx].strip()
                    body = text[split_idx:].strip()
                    return title, body

    return text, ""

def configure_quarto_yml():
    qpath = os.path.join(PROJECT_ROOT, "_quarto.yml")
    if not os.path.exists(qpath):
        print(f"[QuartoConfig] Error: No se encontró {qpath}")
        return
        
    with open(qpath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Idioma Global
    if "lang: es" not in content:
        content = "lang: es\n" + content
        print("  [_quarto.yml] Inyectado 'lang: es' en la raíz.")
        
    # 2. Numeración deshabilitada
    if re.search(r'number-sections:\s*true', content):
        content = re.sub(r'number-sections:\s*true', 'number-sections: false', content)
        print("  [_quarto.yml] Cambiado 'number-sections: true' a 'number-sections: false'.")
    elif "number-sections:" not in content:
        content = re.sub(r'(html:\s*\n)', r'\1    number-sections: false\n', content)
        print("  [_quarto.yml] Agregado 'number-sections: false' en la sección html.")
        
    with open(qpath, "w", encoding="utf-8") as f:
        f.write(content)

def process_chapters(author_map):
    chapters = sorted(glob.glob(os.path.join(PROJECT_ROOT, "0[1-9]-*.qmd")) + glob.glob(os.path.join(PROJECT_ROOT, "1[0-9]-*.qmd")))
    chapters = [c for c in chapters if re.match(r'^(0[1-9]|1[0-4])-capitulo', os.path.basename(c))]

    print(f"\n--- Procesando {len(chapters)} Capítulos in-place ---")

    for fpath in chapters:
        fname = os.path.basename(fpath)
        print(f"Procesando: {fname}...")
        
        # 1. Leer el archivo actual
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        yaml_match = re.match(r'^---\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not yaml_match:
            print(f"  [Error] No se detectó bloque YAML en {fname}")
            continue

        yaml_content = yaml_match.group(1)
        body_content = yaml_match.group(2)

        # 2. Extraer afiliaciones
        affiliations = extract_original_affiliations(fpath, yaml_content, body_content)

        # 3. Parsear autores y re-mapear afiliaciones
        author_block_match = re.search(r'^author:\s*\n((?:\s+-\s*[^\n]+\n)+)', yaml_content, re.MULTILINE)
        
        if author_block_match and "name:" not in author_block_match.group(1):
            authors = re.findall(r'-\s*"([^"]+)"', author_block_match.group(1))
            current_authors = [{"name": auth, "orcid": "", "affiliation": ""} for auth in authors]
        else:
            current_authors = parse_current_authors(yaml_content)

        # Determinar si hay un bloque de afiliaciones de texto plano al inicio del cuerpo para eliminarlo
        heading_match = re.search(r'^#+\s+', body_content, re.MULTILINE)
        if heading_match:
            pre_heading = body_content[:heading_match.start()]
            remaining_body = body_content[heading_match.start():]
            
            has_affiliations = False
            lines = [l.strip() for l in pre_heading.splitlines() if l.strip()]
            for l in lines:
                if ":::" in l:
                    continue
                if re.match(r'^\d+\s*\w+', l) or any(k in l.lower() for k in ["universidad", "departamento", "instituto", "centro", "consultoría", "escuela", "servicio", "facultad", "fundación", "asociación"]):
                    has_affiliations = True
                    break
            
            if has_affiliations:
                body_to_process = remaining_body
            else:
                body_to_process = body_content
        else:
            body_to_process = body_content

        # Re-estructurar autores
        new_author_yaml = "author:\n"
        for aut in current_authors:
            # Limpiar nombre de superíndices previos
            clean_name = re.sub(r'\s*\^[^^]+\^$', '', aut["name"]).strip()
            
            # Extraer números de la afiliación actual
            nums = []
            if aut.get("affiliation"):
                nums = re.findall(r'\^([^^]+)\^', aut["affiliation"])
                if not nums:
                    nums = re.findall(r'\d+', aut["affiliation"])
            
            # Extraer de superíndices del nombre si existen
            name_nums = []
            name_m = re.search(r'\^([^^]+)\^$', aut["name"])
            if name_m:
                name_nums = [n.strip() for n in name_m.group(1).split(",")]
                
            final_nums = name_nums if name_nums else nums
            
            if not final_nums:
                norm_author = normalize_string(clean_name)
                master_aff = author_map.get(norm_author, "")
                if master_aff:
                    for num, aff_text in affiliations.items():
                        matched_part = get_matching_master_affiliation(aff_text, master_aff)
                        if matched_part:
                            final_nums.append(num)
            
            norm_author = normalize_string(clean_name)
            master_aff = author_map.get(norm_author, "")
            
            matched_parts = []
            for num in final_nums:
                part = None
                if master_aff:
                    part = get_matching_master_affiliation(affiliations.get(num, ""), master_aff)
                if not part:
                    part = affiliations.get(num, "")
                if part:
                    matched_parts.append(f"^{num}^{part}")
                    
            zipped = sorted(zip(final_nums, matched_parts), key=lambda x: int(x[0]) if x[0].isdigit() else 999)
            sorted_nums = [x[0] for x in zipped]
            sorted_parts = [x[1] for x in zipped]
            
            aff_str = f"^{','.join(sorted_nums)}^" if sorted_nums else ""
            name_str = f"{clean_name} {aff_str}".strip() if aff_str else clean_name
            affiliation_val = "; ".join(sorted_parts)
            
            new_author_yaml += f"  - name: \"{name_str}\"\n"
            new_author_yaml += f"    orcid: \"{aut.get('orcid', '')}\"\n"
            new_author_yaml += f"    affiliation: \"{affiliation_val}\"\n"

        # Reemplazar el bloque de autores en el YAML
        yaml_content_new = re.sub(
            r'^author:\s*\n(?:[ \t]+.*\n?)*',
            new_author_yaml,
            yaml_content,
            flags=re.MULTILINE
        )

        # Inyectar claves vacías date y doi al final del frontmatter si no existen
        yaml_content_new = yaml_content_new.rstrip() + "\n"
        if not re.search(r'^date:', yaml_content_new, re.MULTILINE):
            yaml_content_new += "date: \"\"\n"
        if not re.search(r'^doi:', yaml_content_new, re.MULTILINE):
            yaml_content_new += "doi: \"\"\n"

        # 4. Envoltura de Resumen y Abstract
        if "::: {#resumen}" not in body_to_process:
            body_to_process = re.sub(
                r'^(##\s+Resumen\s+\{\s*\.unnumbered\s*\}.*?)(?=^##\s+)',
                r'::: {#resumen}\n\1\n:::\n\n',
                body_to_process,
                flags=re.MULTILINE | re.DOTALL
            )
        if "::: {#abstract}" not in body_to_process:
            body_to_process = re.sub(
                r'^(##\s+Abstract\s+\{\s*\.unnumbered\s*\}.*?)(?=^##\s+)',
                r'::: {#abstract}\n\1\n:::\n\n',
                body_to_process,
                flags=re.MULTILINE | re.DOTALL
            )

        # 5. Transformación de Cajas de Información (.caja-box -> callouts)
        box_counter = 0
        def replace_box(match):
            nonlocal box_counter
            box_counter += 1
            inner_content = match.group(1).strip()
            
            caja_match = re.match(r'^\s*\*\*[Cc]aja\s+(\d+)\.?\s*\*\*(.*)', inner_content, re.DOTALL)
            if caja_match:
                caja_num = caja_match.group(1)
                rest = caja_match.group(2).strip()
            else:
                caja_num = str(box_counter)
                rest = inner_content
                
            new_box = f'::: {{#box{box_counter} .callout-important style="background-color: #e3f0fbff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_box += f'**Caja {caja_num}.** {rest}\n'
            new_box += ':::'
            return new_box

        box_pattern = re.compile(r':::\s*\{\s*\.caja-box\s*\}\s*\n(.*?)\n:::', re.DOTALL)
        body_to_process = box_pattern.sub(replace_box, body_to_process)

        # 5.1 Transformación de Puntos Clave (lila claro)
        puntos_counter = 0
        def replace_puntos(match):
            nonlocal puntos_counter
            puntos_counter += 1
            text_content = match.group(1).strip()
            new_puntos = f'::: {{#puntos-clave-{puntos_counter} .callout-important style="background-color: #f4ebffff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_puntos += f'**Puntos clave.** {text_content}\n'
            new_puntos += ':::'
            return new_puntos

        puntos_pattern = re.compile(r'^\|\s*PUNTOS\s+CLAVE\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = puntos_pattern.sub(replace_puntos, body_to_process)

        # 5.2 Transformación de Recomendaciones para tomar decisiones (rosa claro)
        reco_counter = 0
        def replace_reco(match):
            nonlocal reco_counter
            reco_counter += 1
            text_content = match.group(1).strip()
            new_reco = f'::: {{#recomendaciones-{reco_counter} .callout-important style="background-color: #fff0f3ff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_reco += f'**Recomendaciones para tomar decisiones.** {text_content}\n'
            new_reco += ':::'
            return new_reco

        reco_pattern = re.compile(r'^\|\s*RECOMENDACI[OÓ]NES\s+PARA\s+TOMAR\s+DECISIONES\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = reco_pattern.sub(replace_reco, body_to_process)

        # 5.3 Transformación de Retos (verde muy claro)
        retos_counter = 0
        def replace_retos(match):
            nonlocal retos_counter
            retos_counter += 1
            text_content = match.group(1).strip()
            new_retos = f'::: {{#retos-{retos_counter} .callout-important style="background-color: #eafaf1ff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_retos += f'**Retos.** {text_content}\n'
            new_retos += ':::'
            return new_retos

        retos_pattern = re.compile(r'^\|\s*RETOS\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = retos_pattern.sub(replace_retos, body_to_process)

        # 5.4 Transformación de Trabajo a Futuro (amarillo claro)
        trabajo_counter = 0
        def replace_trabajo(match):
            nonlocal trabajo_counter
            trabajo_counter += 1
            text_content = match.group(1).strip()
            new_trabajo = f'::: {{#trabajo-futuro-{trabajo_counter} .callout-important style="background-color: #fffbebff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_trabajo += f'**Trabajo a futuro.** {text_content}\n'
            new_trabajo += ':::'
            return new_trabajo

        trabajo_pattern = re.compile(r'^\|\s*TRABAJO\s+(?:A\s+)?FUTURO\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = trabajo_pattern.sub(replace_trabajo, body_to_process)

        # 6. Numeración Manual In-Place (Jerárquica con Prefijo de Capítulo)
        match_chap = re.search(r'capitulo-(\d+)', fname)
        chap_num = int(match_chap.group(1)) if match_chap else 1

        lines = body_to_process.splitlines()
        new_lines = []
        h2_counter = 0
        h3_counter = 0
        
        for line in lines:
            if line.startswith("#"):
                line_lower = line.lower()
                
                # Ignorar encabezados de Resumen o Abstract
                if "resumen" in line_lower or "abstract" in line_lower:
                    new_lines.append(line)
                    continue
                
                # Nivel H2 (##)
                if line.startswith("## "):
                    h2_counter += 1
                    h3_counter = 0
                    line_clean = re.sub(r'\s*\{\s*\.unnumbered\s*\}', '', line)
                    cleaned_title = re.sub(r'^##\s*(?:\d+(?:\.\d+)*\.?\s*)?', '', line_clean).strip()
                    new_line = f"## {chap_num}.{h2_counter} {cleaned_title}"
                    new_lines.append(new_line)
                
                # Nivel H3 (###)
                elif line.startswith("### "):
                    h3_counter += 1
                    line_clean = re.sub(r'\s*\{\s*\.unnumbered\s*\}', '', line)
                    cleaned_title = re.sub(r'^###\s*(?:\d+(?:\.\d+)*\.?\s*)?', '', line_clean).strip()
                    new_line = f"### {chap_num}.{h2_counter}.{h3_counter} {cleaned_title}"
                    new_lines.append(new_line)
                
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        body_to_process = "\n".join(new_lines)

        # 7. Escribir archivo de vuelta
        final_content = f"---\n{yaml_content_new.rstrip()}\n---\n\n{body_to_process}"
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(final_content)
        print(f"  [Completado] {fname} migrado con éxito.")

def purge_cache():
    folders_to_delete = [os.path.join(PROJECT_ROOT, "_book"), os.path.join(PROJECT_ROOT, ".quarto")]
    print("\n--- 3. Limpieza de Caché Interna ---")
    for folder in folders_to_delete:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"  [Completado] Carpeta eliminada con éxito: {folder}/")
            except Exception as e:
                print(f"  [Error] No se pudo eliminar la carpeta {folder}: {e}")
        else:
            print(f"  [Info] La carpeta {folder}/ no existe o ya fue eliminada.")

def main():
    print("=========================================================")
    print("INICIANDO HERRAMIENTA MAESTRA DE MIGRACIÓN - UNGRD")
    print("=========================================================")
    
    # 1. Configurar archivo _quarto.yml
    print("\n--- 1. Configurando _quarto.yml ---")
    configure_quarto_yml()
    
    # 2. Cargar autores y procesar capítulos
    author_map = load_master_authors()
    if author_map:
        process_chapters(author_map)
        
    # 3. Purgar caché al finalizar
    purge_cache()
    
    print("\n=========================================================")
    print("¡MIGRACIÓN Y CONSOLIDACIÓN COMPLETADAS CON ÉXITO!")
    print("=========================================================")

if __name__ == "__main__":
    main()
