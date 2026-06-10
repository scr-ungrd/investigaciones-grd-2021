import zipfile
import xml.etree.ElementTree as ET
import os
import glob
import re

def read_xlsx(file_path):
    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        shared_strings = []
        if 'xl/sharedStrings.xml' in zip_ref.namelist():
            ss_content = zip_ref.read('xl/sharedStrings.xml')
            ss_root = ET.fromstring(ss_content)
            for t_elem in ss_root.findall('.//ns:t', ns):
                shared_strings.append(t_elem.text)
                
        sheet_content = zip_ref.read('xl/worksheets/sheet1.xml')
        sheet_root = ET.fromstring(sheet_content)
        
        rows = []
        for row in sheet_root.findall('.//ns:row', ns):
            row_cells = {}
            for cell in row.findall('ns:c', ns):
                cell_ref = cell.get('r')
                col_letter = ''.join([c for c in cell_ref if c.isalpha()])
                cell_type = cell.get('t')
                val_elem = cell.find('ns:v', ns)
                val = ""
                if val_elem is not None:
                    val = val_elem.text
                    if cell_type == 's':
                        idx = int(val)
                        val = shared_strings[idx] if idx < len(shared_strings) else ""
                row_cells[col_letter] = val
            rows.append(row_cells)
            
        return rows

def clean_name(name):
    if not name:
        return ""
    # Remove superscript annotations like ^1^ or ^1,2,3^
    name = re.sub(r'\s*\^.*?\^', '', name)
    name = name.strip()
    return name

def normalize(text):
    import unicodedata
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r'\s+', ' ', text).lower().strip()
    return text

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

def main():
    # Load Excel data
    excel_rows = read_xlsx('data/orcid-2021.xlsx')
    orcid_map = {}
    for r in excel_rows[1:]:
        name = r.get('A', '').strip()
        orcid = r.get('B', '').strip()
        if name:
            orcid_map[normalize(name)] = (name, orcid)

    # Scan and update QMD files
    qmd_files = sorted(glob.glob("*.qmd"))
    qmd_files = [f for f in qmd_files if re.match(r'^(0[1-9]|1[0-4])-capitulo', os.path.basename(f))]

    print("=== Actualización de ORCIDs en capítulos ===")
    
    for fpath in qmd_files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        frontmatter_match = re.match(r'^---\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not frontmatter_match:
            print(f"[Error] No frontmatter in {fname}")
            continue
            
        yaml_content = frontmatter_match.group(1)
        body_content = frontmatter_match.group(2)
        
        current_authors = parse_current_authors(yaml_content)
        if not current_authors:
            continue
            
        new_author_yaml = "author:\n"
        updates = []
        for aut in current_authors:
            clean_n = clean_name(aut["name"])
            norm = normalize(clean_n)
            
            orcid = aut.get("orcid", "")
            if norm in orcid_map:
                excel_name, excel_orcid = orcid_map[norm]
                if orcid != excel_orcid:
                    updates.append(f"  - {clean_n}: '{orcid}' -> '{excel_orcid}'")
                    orcid = excel_orcid
            else:
                print(f"  [Advertencia] {clean_n} no se encontró en el archivo Excel.")
                
            new_author_yaml += f"  - name: \"{aut['name']}\"\n"
            new_author_yaml += f"    orcid: \"{orcid}\"\n"
            new_author_yaml += f"    affiliation: \"{aut['affiliation']}\"\n"
            
        if updates:
            print(f"\nArchivo: {fname}")
            for u in updates:
                print(u)
                
            # Replace authors block
            yaml_content_new = re.sub(
                r'^author:\s*\n(?:[ \t]+.*\n?)*',
                new_author_yaml,
                yaml_content,
                flags=re.MULTILINE
            )
            
            new_content = f"---\n{yaml_content_new.rstrip()}\n---\n\n{body_content}"
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)
        else:
            print(f"Archivo: {fname} - Sin cambios (ORCIDs ya actualizados)")

if __name__ == "__main__":
    main()
