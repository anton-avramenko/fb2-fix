import xml.etree.ElementTree as ET
import re
import argparse

def is_junk_paragraph(text):
    """
    Determines if a paragraph is likely OCR noise and should be removed entirely.
    """
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
        return True
    return False

def clean_and_merge_text(paragraphs):
    """
    Merges and cleans the text from a list of paragraph elements.
    """
    full_text = ""
    for p in paragraphs:
        text = ''.join(p.itertext()).strip()
        # Handle hyphenation at the end of a line
        if full_text.endswith('-'):
            full_text = full_text[:-1] + text
        else:
            full_text += " " + text

    # Clean up trailing numbers and other artifacts from the merged text
    full_text = re.sub(r'\s*\[\d+\]\s*$', '', full_text) # Removes [1], [2] etc. at the end
    full_text = re.sub(r'\s*\d+\s*$', '', full_text) # Removes trailing numbers
    return full_text.strip()


def clean_fb2_file(input_path, output_path):
    """
    Cleans an FB2 file by removing OCR noise and merging fragmented paragraphs.
    """
    ET.register_namespace('', "http://www.gribuser.ru/xml/fictionbook/2.0")
    namespace = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}

    tree = ET.parse(input_path)
    root = tree.getroot()
    body = root.find('fb:body', namespace)

    if body is None:
        return

    for section in body.findall('.//fb:section', namespace):
        # First, remove junk paragraphs
        paragraphs_to_remove = [p for p in section.findall('fb:p', namespace) if is_junk_paragraph(''.join(p.itertext()).strip())]
        for p in paragraphs_to_remove:
            section.remove(p)

        # Then, merge and clean remaining paragraphs
        new_children = []
        para_buffer = []
        for child in section:
            if child.tag == f"{{{namespace['fb']}}}p":
                para_buffer.append(child)
            else:
                if para_buffer:
                    new_text = clean_and_merge_text(para_buffer)
                    new_p = ET.Element('p')
                    new_p.text = new_text
                    new_children.append(new_p)
                    para_buffer = []
                new_children.append(child)

        if para_buffer:
            new_text = clean_and_merge_text(para_buffer)
            new_p = ET.Element('p')
            new_p.text = new_text
            new_children.append(new_p)

        # Replace the old children of the section with the new, cleaned ones
        section.clear()
        section.extend(new_children)


    tree.write(output_path, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean FB2 files by removing OCR noise.')
    parser.add_argument('input_file', help='The path to the input FB2 file.')
    parser.add_argument('output_file', help='The path to save the cleaned FB2 file.')
    args = parser.parse_args()

    clean_fb2_file(args.input_file, args.output_file)
    print(f"Cleaned file saved to {args.output_file}")