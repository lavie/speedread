import argparse
import json
import re
from jinja2 import Environment, FileSystemLoader

def read_json_summaries(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def markdown_to_html(text):
    # Convert bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert numbered lists
    text = re.sub(r'^\d+\.\s(.*)$', r'<ol><li>\1</li></ol>', text, flags=re.MULTILINE)
    text = re.sub(r'</ol>\s*<ol>', '', text)  # Merge adjacent <ol> tags
    
    # Convert bullet points
    text = re.sub(r'^\*\s(.*)$', r'<ul><li>\1</li></ul>', text, flags=re.MULTILINE)
    text = re.sub(r'</ul>\s*<ul>', '', text)  # Merge adjacent <ul> tags
    
    return text

def create_html_content(book_data):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('book_summary.html')

    chapters = []
    for i, chapter in enumerate(book_data['summaries'], 1):
        formatted_summary = ''.join([f'<p>{markdown_to_html(p.strip())}</p>' for p in chapter['summary'].split('\n\n') if p.strip()])
        chapters.append({
            'number': i,
            'name': chapter['chapter_title'],
            'content': formatted_summary
        })

    return template.render(
        title=book_data['title'],
        author=book_data['author'],
        chapters=chapters,
        book_title=book_data['title'],  # Add this line
        book_author=book_data['author']  # Add this line
    )

def main():
    parser = argparse.ArgumentParser(description='Compile chapter summaries into a single HTML file.')
    parser.add_argument('summary_file', help='JSON file containing the combined summaries')
    parser.add_argument('-o', '--output', default='book_summary.html', help='Output HTML file name')
    args = parser.parse_args()

    book_data = read_json_summaries(args.summary_file)
    html_content = create_html_content(book_data)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Summary compiled and saved to {args.output}")

if __name__ == "__main__":
    main()
