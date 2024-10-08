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
        
        # Find files containing NavPoint elements
        nav_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'navPoint' in content:
                        nav_files.append(file_path)
        
        # If more than one file contains NavPoint, abort
        if len(nav_files) != 1:
            raise ValueError(f"Expected 1 navigation file, found {len(nav_files)}")
        
        nav_file = nav_files[0]
        
        # Parse the navigation file
        with open(nav_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'xml')
        
        # Extract metadata
        metadata = {}
        metadata['title'] = soup.find('docTitle').text.strip() if soup.find('docTitle') else "Unknown Title"
        metadata['author'] = soup.find('docAuthor').text if soup.find('docAuthor') else "Unknown Author"
        
        # Extract chapters
        chapters = []
        for navPoint in soup.find_all('navPoint'):
            label = navPoint.find('text').string
            content = navPoint.find('content')
            if content:
                src = content.get('src', '').split('#')[0]
                chapters.append({"title": label, "src": src})
        
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
