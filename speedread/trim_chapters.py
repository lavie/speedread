import argparse
import json
import os
from openai import OpenAI

def trim_chapters(metadata):
    client = OpenAI()
    
    prompt = """
    You are an AI assistant tasked with identifying the main chapters of a book.
    Given a JSON structure containing book metadata and chapters, your job is to:
    1. Identify the main chapters of the book. Examples of chapters that are not considered main are prefaces, introductions, appendices, endnotes, about the author, etc.
    2. Identify the first main chapter and the last. Keep all chapters in between them and discard all the rest. Never discard a chapter between the first and the last main chapters even if it does not look to be a main chapter.
    3. Return a new JSON structure with only the main chapters.

    Use these guidelines:
    - Main chapters usually have numeric or clear sequential titles.
    - Chapters at the beginning like "Preface", "Introduction", "Prologue" are usually not main chapters.
    - Chapters at the end like "Appendix", "Notes", "Bibliography", "Index" are usually not main chapters.
    - If in doubt, err on the side of inclusion.

    Here's the book metadata and chapters:
    {json_data}

    Please return only a valid JSON structure with the trimmed chapters, maintaining the original format.
    """

    content = prompt.format(json_data=json.dumps(metadata, indent=2))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that processes book metadata."},
            {"role": "user", "content": content }
        ],
        temperature=0.2,
    )

    try:
        trimmed_metadata = json.loads(response.choices[0].message.content)
        return trimmed_metadata
    except json.JSONDecodeError:
        print("Error: The AI response was not valid JSON. Using original metadata.")
        return metadata

def main():
    parser = argparse.ArgumentParser(description='Trim non-chapter content from book metadata JSON.')
    parser.add_argument('input_json', help='Path to the input JSON file')
    parser.add_argument('-o', '--output', help='Path to save the output JSON file', default=None)
    args = parser.parse_args()

    # Read input JSON
    with open(args.input_json, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Trim chapters
    trimmed_metadata = trim_chapters(metadata)

    # Output result
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(trimmed_metadata, f, ensure_ascii=False, indent=2)
        print(f'Trimmed metadata saved to {args.output}')
    else:
        print(json.dumps(trimmed_metadata, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
