import os
import re

directory = "/home/nia/scr-ungrd/investigaciones-grd-2021"
files = [f for f in os.listdir(directory) if f.endswith(".qmd")]

color_line = 'title-block-banner-color: "#151550ff"'

for filename in files:
    filepath = os.path.join(directory, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update YAML color
    yaml_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if yaml_match:
        yaml_block = yaml_match.group(1)
        if 'title-block-banner-color:' not in yaml_block:
            new_yaml = yaml_block.rstrip() + f"\n{color_line}\n"
            content = content.replace(yaml_block, new_yaml)
        else:
            new_yaml = re.sub(r'title-block-banner-color:.*', color_line, yaml_block)
            content = content.replace(yaml_block, new_yaml)
    else:
        # Create new YAML block at the beginning
        content = f"---\n{color_line}\n---\n\n" + content

    # 2. Replace **Resumen** and **Abstract**
    content = re.sub(r'\*\*Resumen\s*\*\*', '## Resumen {.unnumbered}', content)
    content = re.sub(r'\*\*Abstract\s*\*\*', '## Abstract {.unnumbered}', content)

    # 3. Replace Keywords / Key words with **Keywords**
    content = re.sub(r'(?<![#*])\bKey\s+words\b(?![#*])', '**Keywords**', content, flags=re.IGNORECASE)
    content = re.sub(r'(?<![#*])\bKeywords\b(?![#*])', '**Keywords**', content, flags=re.IGNORECASE)
    content = re.sub(r'\*\*Keywords\s+\*\*', '**Keywords**', content)
    content = re.sub(r'\*\*Key\s+words\s+\*\*', '**Keywords**', content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Processed {len(files)} files.")
