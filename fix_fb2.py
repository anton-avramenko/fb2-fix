import xml.etree.ElementTree as ET
import re
import argparse

def clean_text_node(text):
    """
    Cleans text by removing trailing numbers and artifacts.
    """
    if text is None:
        return ""
    # Remove trailing numbers and artifacts
    text = re.sub(r'\s*\d+$', '', text)
    text = re.sub(r'\s*R \d+R \d+R \d+R \d+$', '', text)
    # Correctly handle hyphenated words
    text = text.replace('- ', '')
    return text

def merge_paragraphs(section, namespace):
    """
    Merges consecutive paragraphs within a section.
    """
    new_children = []
    current_p = None

    for elem in section:
        if elem.tag == f"{{{namespace['fb']}}}p":
            if current_p is None:
                current_p = elem
            else:
                # Append text and children from the current elem to current_p
                if elem.text:
                    if current_p.text is None:
                        current_p.text = ""
                    current_p.text += " " + elem.text
                for child in elem:
                    current_p.append(child)
                if elem.tail:
                    if current_p.text is None:
                        current_p.text = ""
                    current_p.text += elem.tail
        else:
            if current_p is not None:
                new_children.append(current_p)
                current_p = None
            new_children.append(elem)

    if current_p is not None:
        new_children.append(current_p)

    # Clean text in the merged paragraphs
    for p in new_children:
        if p.tag == f"{{{namespace['fb']}}}p":
            if p.text:
                p.text = clean_text_node(p.text)
            for child in p:
                if child.tail:
                    child.tail = clean_text_node(child.tail)

    section.clear()
    section.extend(new_children)


def clean_fb2_file(input_path, output_path):
    """
    Cleans an FB2 file by removing noisy paragraphs and merging fragmented ones.
    """
    ET.register_namespace('', "http://www.gribuser.ru/xml/fictionbook/2.0")
    namespace = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}

    tree = ET.parse(input_path)
    root = tree.getroot()
    body = root.find('fb:body', namespace)

    if body is None:
        return

    for section in body.findall('.//fb:section', namespace):
        paragraphs_to_remove = []
        for p in section.findall('fb:p', namespace):
            text = ''.join(p.itertext()).strip()

            if (
                text == "3rd Pass Pages" or
                "ManInMyBasemnt_HCtext3P" in text or
                re.match(r'S \d+S \d+', text) or
                re.match(r'R \d+R \d+', text) or
                re.match(r'\d+ C\d+ C\d+', text) or
                re.match(r'\d+ S\d+ S\d+', text) or
                re.match(r'S \d+S \d+S \d+S \d+', text) or
                re.match(r'R \d+R \d+R \d+R \d+', text) or
                (len(text) < 10 and re.fullmatch(r'[\d-]+', text))
            ):
                paragraphs_to_remove.append(p)
                continue

        for p in set(paragraphs_to_remove):
            if p in section:
                section.remove(p)

        merge_paragraphs(section, namespace)

    tree.write(output_path, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean FB2 files by removing OCR noise.')
    parser.add_argument('input_file', help='The path to the input FB2 file.')
    parser.add_argument('output_file', help='The path to save the cleaned FB2 file.')
    args = parser.parse_args()

    clean_fb2_file(args.input_file, args.output_file)
    print(f"Cleaned file saved to {args.output_file}")