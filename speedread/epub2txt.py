import argparse
import json
import os
import tempfile
import zipfile
from bs4 import BeautifulSoup
from speedread.epub_metadata import extract_toc_from_epub
from speedread.trim_chapters import trim_chapters

def extract_chapter_content(temp_dir, chapter_src):
    chapter_path = os.path.join(temp_dir, chapter_src)
    if os.path.exists(chapter_path):
        with open(chapter_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f, 'html.parser')
            return soup.get_text()
    else:
        print(f"Cannot find chapter file: {chapter_path}")
    return ""

def epub_to_structured_text(epub_path):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract EPUB contents
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Extract metadata
            metadata = extract_toc_from_epub(epub_path)
            
            # Trim chapters
            trimmed_metadata = trim_chapters(metadata)
            print(trimmed_metadata)
            
            # Extract chapter contents
            for chapter in trimmed_metadata['chapters']:
                chapter['content'] = extract_chapter_content(temp_dir, chapter['src'])
                del chapter['src']  # Remove the 'src' key as it's no longer needed
            
            # Cleanup phase: discard chapters with content less than 1KB
            trimmed_metadata['chapters'] = [
                chapter for chapter in trimmed_metadata['chapters']
                if len(chapter['content'].encode('utf-8')) >= 1024
            ]
            
            return trimmed_metadata
    except Exception as e:
        print(f"Error processing EPUB file: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Convert EPUB to structured JSON with metadata and content.')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Path to save the output JSON file', default=None)
    args = parser.parse_args()

    structured_content = epub_to_structured_text(args.epub_file)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(structured_content, f, ensure_ascii=False, indent=2)
        print(f'Structured content saved to {args.output}')
    else:
        print(json.dumps(structured_content, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
