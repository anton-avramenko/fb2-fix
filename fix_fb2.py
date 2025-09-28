import xml.etree.ElementTree as ET
import re
import argparse

def clean_fb2_file(input_path, output_path):
    """
    Cleans an FB2 file by removing noisy paragraphs from OCR and merging fragmented ones.
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

            # Define patterns for noisy paragraphs
            if (
                re.fullmatch(r'[\d-]+', text) or
                text == "3rd Pass Pages" or
                "ManInMyBasemnt_HCtext3P" in text or
                re.match(r'S \d+S \d+', text) or
                re.match(r'R \d+R \d+', text) or
                re.match(r'\d+ C\d+ C\d+', text) or
                re.match(r'\d+ S\d+ S\d+', text) or
                re.match(r'S \d+S \d+S \d+S \d+', text) or
                re.match(r'R \d+R \d+R \d+R \d+', text)
            ):
                paragraphs_to_remove.append(p)

        for p in paragraphs_to_remove:
            # A paragraph might be a child of a section or another element, so we need to find its parent.
            parent_map = {c: p for p in root.iter() for c in p}
            parent = parent_map.get(p)
            if parent is not None:
                parent.remove(p)

    # Merging consecutive paragraphs
    for section in body.findall('.//fb:section', namespace):
        merged_children = []
        text_buffer = ""
        for p in section.findall('fb:p', namespace):
            text_buffer += " " + ''.join(p.itertext()).strip()
            if text_buffer.endswith('.'):
                new_p = ET.Element('p')
                new_p.text = text_buffer.strip()
                merged_children.append(new_p)
                text_buffer = ""

        # Add any remaining text in the buffer as a new paragraph
        if text_buffer.strip():
            new_p = ET.Element('p')
            new_p.text = text_buffer.strip()
            merged_children.append(new_p)

        # Replace the old paragraphs with the new merged ones
        for p in section.findall('fb:p', namespace):
            section.remove(p)
        section.extend(merged_children)


    tree.write(output_path, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean FB2 files by removing OCR noise.')
    parser.add_argument('input_file', help='The path to the input FB2 file.')
    parser.add_argument('output_file', help='The path to save the cleaned FB2 file.')
    args = parser.parse_args()

    clean_fb2_file(args.input_file, args.output_file)
    print(f"Cleaned file saved to {args.output_file}")