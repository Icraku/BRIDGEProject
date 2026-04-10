import re

with open("markdown_exports/extractions_NAR_63000001_page_1_base.md", "r", encoding="utf-8") as f:
    md = f.read()

def clean_markdown(md):
    """
    Rmoves the backticks in the markdown
    :param md:
    :return:
    """
    md = md.replace("`", "")
    md = md.replace("<br>", " ")
    return md

def parse_checkbox_field(text):
    """
    Parse the checkbox field
    :param text:
    :return:
    """
    pattern = r'([A-Za-z0-9<>/= ]+)\s*\[(x| )\]'
    matches = re.findall(pattern, text)

    if not matches:
        return text.strip()

    result = {}
    for label, mark in matches:
        result[label.strip()] = (mark.lower() == "x")

    return result

def parse_markdown_table(md):
    """
    Parse the table for 2 column and 4 column tables
    :param md:
    :return:
    """
    lines = md.split("\n")
    data = {}

    for line in lines:
        if "|" not in line or "---" in line:
            continue

        cells = [c.strip() for c in line.split("|") if c.strip()]

        # 2-column table
        if len(cells) == 2:
            key = re.sub(r"\*\*", "", cells[0])
            value = cells[1]

            data[key] = parse_checkbox_field(value)

        # 4-column table
        elif len(cells) == 4:
            key1 = re.sub(r"\*\*", "", cells[0])
            val1 = cells[1]
            key2 = re.sub(r"\*\*", "", cells[2])
            val2 = cells[3]

            data[key1] = parse_checkbox_field(val1)
            data[key2] = parse_checkbox_field(val2)

    return data

def markdown_to_json(md):
    md_text = clean_markdown(md)
    parsed = parse_markdown_table(md_text)
    return parsed