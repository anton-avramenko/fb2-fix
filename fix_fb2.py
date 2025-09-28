import xml.etree.ElementTree as ET
import re
import argparse

def clean_fb2_file(input_path, output_path):
    """
    Cleans an FB2 file by removing noisy paragraphs from OCR.
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

            # Heuristic 1: Mostly numbers
            if len(text) > 0 and len(re.findall(r'\d', text)) > 0 and len(text) > 0 and (len(re.findall(r'\d', text)) / len(text)) > 0.5:
                paragraphs_to_remove.append(p)
                continue

            # Heuristic 2: Short lines with numbers (likely page numbers or artifacts)
            # but preserve chapter headings like <strong>1</strong>
            if len(text) < 10 and re.search(r'\d', text):
                is_chapter_heading = False
                strong_tag = p.find('fb:strong', namespace)
                if strong_tag is not None:
                    if re.fullmatch(r'\d+', ''.join(strong_tag.itertext()).strip()):
                        is_chapter_heading = True
                if not is_chapter_heading:
                    paragraphs_to_remove.append(p)
                    continue

            # Heuristic 3: Text ending with emphasized numbers (likely page footers)
            last_element = p[-1] if list(p) else None
            if last_element is not None and last_element.tag == f"{{{namespace['fb']}}}emphasis":
                emphasis_text = ''.join(last_element.itertext()).strip()
                if re.fullmatch(r'\d+', emphasis_text):
                    paragraphs_to_remove.append(p)
                    continue

            # Specific known patterns
            if (
                text == "3rd Pass Pages" or
                "ManInMyBasemnt_HCtext3P" in text or
                re.match(r'S \d+S \d+', text) or
                re.match(r'R \d+R \d+', text) or
                re.match(r'\d+ C\d+ C\d+', text) or
                re.match(r'\d+ S\d+ S\d+', text) or
                re.match(r'S \d+S \d+S \d+S \d+', text) or
                re.match(r'R \d+R \d+R \d+R \d+', text) or
                re.fullmatch(r'[\d-]+', text)
            ):
                paragraphs_to_remove.append(p)
                continue

        for p in set(paragraphs_to_remove):
            # Check if the parent of p is the current section before removing
            if p in section:
                section.remove(p)

    tree.write(output_path, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean FB2 files by removing OCR noise.')
    parser.add_argument('input_file', help='The path to the input FB2 file.')
    parser.add_argument('output_file', help='The path to save the cleaned FB2 file.')
    args = parser.parse_args()

    clean_fb2_file(args.input_file, args.output_file)
    print(f"Cleaned file saved to {args.output_file}")