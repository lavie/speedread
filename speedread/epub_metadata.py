import logging
import os
import tempfile
import zipfile
import json
import argparse
from bs4 import BeautifulSoup

def extract_toc_from_epub(epub_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip the EPUB file
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find content.opf and navigation files
        content_opf = None
        nav_file = None
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file == 'content.opf':
                    content_opf = file_path
                elif 'toc' in file.lower() and file.endswith('.ncx'):
                    nav_file = file_path
        
        if not content_opf:
            raise ValueError("content.opf file not found in EPUB")
        if not nav_file:
            raise ValueError("Navigation file not found in EPUB")
        
        # Parse content.opf file
        with open(content_opf, 'r', encoding='utf-8') as f:
            opf_soup = BeautifulSoup(f, 'xml')
        
        # Extract metadata
        metadata = {}
        metadata['title'] = opf_soup.find('dc:title').text.strip() if opf_soup.find('dc:title') else "Unknown Title"
        metadata['author'] = opf_soup.find('dc:creator').text.strip() if opf_soup.find('dc:creator') else "Unknown Author"
        
        # Parse the navigation file
        with open(nav_file, 'r', encoding='utf-8') as f:
            nav_soup = BeautifulSoup(f, 'xml')
        
        # Extract chapters
        chapters = []
        for navPoint in nav_soup.find_all('navPoint'):
            label = navPoint.find('text').string
            content = navPoint.find('content')
            if content:
                src = content.get('src', '').split('#')[0]
                chapter = {"title": label, "src": src}
                logging.info(f'Found chapter: {chapter}')
                chapters.append(chapter)
            else:
                logging.warning(f'Chapter without content: {label}')
        
        metadata['chapters'] = chapters
        
        return metadata

def main():
    parser = argparse.ArgumentParser(description='Extract metadata from EPUB file.')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Path to save the output JSON file', default=None)
    args = parser.parse_args()

    try:
        metadata = extract_toc_from_epub(args.epub_file)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f'Metadata saved to {args.output}')
        else:
            print(json.dumps(metadata, ensure_ascii=False, indent=2))
    
    except Exception as e:
        print(f"Error processing EPUB file: {e}")

if __name__ == "__main__":
    main()
