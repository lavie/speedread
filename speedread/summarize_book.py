import argparse
from openai import OpenAI
import os
import json
from tqdm import tqdm

MODEL = "gpt-4-turbo"  # or "gpt-3.5-turbo" if GPT-4 is not available

SUMMARIZER_PROMPT = """
This GPT is a book summarizer specializing in condensing chapters into succinct, engaging summaries that can be consumed quickly, effectively compressing the content to about one-tenth of its original length. It highlights key anecdotes, essential facts, and intriguing, unintuitive observations or opinions, focusing on the most memorable and impactful parts of each text. The GPT prioritizes clarity, brevity, and the preservation of the original intent and tone of the book, while ensuring that all critical insights and unique points are emphasized for a comprehensive and captivating summary.
"""

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def summarize_chapter(client, chapter_content, chapter_title):
    prompt = f"{SUMMARIZER_PROMPT}\n\nChapter title: {chapter_title}\nChapter text to summarize:\n{chapter_content}\n\nPlease provide a concise summary of this chapter:"
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SUMMARIZER_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(description='Summarize a book chapter by chapter using GPT-4.')
    parser.add_argument('json_file', help='Path to the JSON file containing book content')
    parser.add_argument('-o', '--output_dir', help='Directory to save the output summaries', default='summaries')
    args = parser.parse_args()

    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    client = OpenAI()
    book_data = read_json_file(args.json_file)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    summaries = []
    for chapter in tqdm(book_data['chapters'], desc="Summarizing Chapters"):
        chapter_summary = summarize_chapter(client, chapter['content'], chapter['title'])
        
        output_file = os.path.join(args.output_dir, f"chapter_{chapter['title']}_summary.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Chapter: {chapter['title']}\n\n")
            f.write(chapter_summary)
        
        chapter_number = str(len(summaries) + 1).zfill(2)
        output_file = os.path.join(args.output_dir, f"chapter_{chapter_number}_summary.json")
        summary_data = {
            "chapter_title": chapter['title'],
            "summary": chapter_summary
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        summaries.append(summary_data)

    # Save the combined summaries
    summaries_file = os.path.join(args.output_dir, "summaries.json")
    with open(summaries_file, 'w', encoding='utf-8') as f:
        json.dump({
            "title": book_data['title'],
            "author": book_data['author'],
            "summaries": summaries
        }, f, ensure_ascii=False, indent=2)

    print(f"\nAll chapter summaries have been saved to the '{args.output_dir}' directory.")
    print(f"Combined summaries saved to {summaries_file}")

if __name__ == "__main__":
    main()
