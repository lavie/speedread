import argparse
import os
from pathlib import Path
import json
import logging
import asyncio

from speedread.utils import sanitize_filename

from speedread.epub2json import epub_to_json
from speedread.trim_chapters import trim_chapters
from speedread.summarize_book import summarize_chapter
from speedread.compile_summaries import create_html_content
from speedread.batch_text_to_speech import process_chapter
from speedread.text_to_speech import VALID_VOICES
from speedread.create_audiobook import create_audiobook

from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def summarize_chapters(client, chapters, max_concurrency):
    async def summarize(chapter):
        return {
            "chapter_title": chapter['title'],
            "summary": await asyncio.to_thread(summarize_chapter, client, chapter['content'], chapter['title'])
        }

    semaphore = asyncio.Semaphore(max_concurrency)
    async def bounded_summarize(chapter):
        async with semaphore:
            return await summarize(chapter)

    tasks = [bounded_summarize(chapter) for chapter in chapters]
    return await asyncio.gather(*tasks)

async def async_main():
    logging.getLogger("openai").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description='Convert EPUB to HTML summary and audiobook.')
    parser.add_argument('epub_file', help='Path to the input EPUB file')
    parser.add_argument('--audiobook', action='store_true', help='Create audiobook (optional)')
    parser.add_argument('--concurrency', type=int, default=5, help='Number of concurrent summarization operations')
    parser.add_argument('--voice', type=str, choices=VALID_VOICES, default="alloy",
                        help='Voice to use for text-to-speech (default: alloy)')
    args = parser.parse_args()

    epub_path = Path(args.epub_file)
    if not epub_path.exists():
        logging.error(f"Error: File {epub_path} does not exist.")
        return

    safe_title = sanitize_filename(epub_path.stem)
    output_dir = epub_path.parent / f"{safe_title}_speedread"
    output_dir.mkdir(exist_ok=True)

    content_json_file = output_dir / f"{safe_title}_content.json"
    markdown_file = output_dir / f"{safe_title}_content.md"
    summary_json_file = output_dir / f"{safe_title}_summary.json"
    html_file = output_dir / f"{safe_title}_summary.html"

    structured_content = None
    if content_json_file.exists():
        logging.info("Loading existing content from JSON...")
        with open(content_json_file, 'r', encoding='utf-8') as f:
            structured_content = json.load(f)
    else:
        logging.info("Step 1: Parsing EPUB...")
        structured_content = epub_to_json(str(epub_path))
        if not structured_content:
            logging.error("Error: Failed to convert EPUB to structured text.")
            return
        
        # Save as JSON for internal use
        with open(content_json_file, 'w', encoding='utf-8') as f:
            json.dump(structured_content, f, ensure_ascii=False, indent=2)
        logging.info(f"Content JSON saved to: {content_json_file}")

        # Save as markdown for human reading
        markdown_content = f"# {structured_content['title']}\nby {structured_content['author']}\n\n"
        for chapter in structured_content['chapters']:
            markdown_content += f"# {chapter['title']}\n{chapter['content']}\n\n"
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        logging.info(f"Human-readable markdown saved to: {markdown_file}")

    title = structured_content['title']
    author = structured_content['author']
    logging.info(f"Book: '{title}' by {author}")
    summaries = None


    if summary_json_file.exists():
        logging.info("Loading existing summary...")
        with open(summary_json_file, 'r') as f:
            summary_data = json.load(f)
        summaries = summary_data['summaries']
    else:

        logging.info(f"Original chapter count: {len(structured_content['chapters'])}")
        logging.info("Step 2: Trimming chapters...")
        content_for_trimming = {
            'title': structured_content['title'],
            'author': structured_content['author'],
            'chapters': [{'title': chapter['title']} for chapter in structured_content['chapters']]
        }
        trimmed_content = trim_chapters(content_for_trimming)
        
        full_trimmed_content = {
            'title': trimmed_content['title'],
            'author': trimmed_content['author'],
            'chapters': []
        }
        for trimmed_chapter in trimmed_content['chapters']:
            for full_chapter in structured_content['chapters']:
                if trimmed_chapter['title'] == full_chapter['title']:
                    full_trimmed_content['chapters'].append(full_chapter)
                    break
        
        chapter_count = len(full_trimmed_content['chapters'])
        logging.info(f"Trimmed chapter count: {chapter_count}")

        # Display chapters and get confirmation
        logging.info("\nChapters to be summarized:")
        for i, chapter in enumerate(full_trimmed_content['chapters'], 1):
            word_count = len(chapter['content'].split())
            logging.info(f"{i}. {chapter['title']} ({word_count} words)")
        
        response = input("\nWould you like to proceed with summarizing these chapters? (y/n): ").lower().strip()
        if response != 'y':
            logging.info("Summarization cancelled.")
            return

        logging.info("Step 3: Summarizing book...")
        client = OpenAI()
        summaries = await summarize_chapters(client, full_trimmed_content['chapters'], args.concurrency)

        # Save summary JSON
        with open(summary_json_file, 'w') as f:
            json.dump({
                "title": title,
                "author": author,
                "summaries": summaries
            }, f)
        logging.info(f"Summary JSON saved to: {summary_json_file}")

    logging.info("Step 4: Compiling summaries...")
    html_content = create_html_content({
        "title": title,
        "author": author,
        "summaries": summaries
    })

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logging.info(f"HTML summary saved to: {html_file}")

    if args.audiobook:
        logging.info("Ready to start text-to-speech conversion.")
        response = input("Would you like to proceed with creating the audiobook? (y/n): ").lower().strip()
        if response != 'y':
            logging.info("Audiobook creation cancelled.")
            return
            
        logging.info("Step 5: Converting text to speech...")
        audio_dir = output_dir / "audio_chapters"
        audio_dir.mkdir(exist_ok=True)

        client = OpenAI()
        semaphore = asyncio.Semaphore(args.concurrency)
        tasks = []

        for i, chapter in enumerate(summaries, start=1):
            chapter_with_number = {
                'number': i,
                'chapter_title': chapter['chapter_title'],
                'summary': chapter['summary']
            }
            task = asyncio.create_task(process_chapter(client, chapter_with_number, audio_dir, semaphore, args.voice))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        audio_files = [result for result in results if result]

        logging.info(f"Number of audio files generated: {len(audio_files)}")
        for audio_file in audio_files:
            logging.info(f"Generated audio file: {audio_file}")

        if not audio_files:
            logging.error("Error: No audio files were generated. Skipping audiobook creation.")
            logging.error("Please check the OpenAI API key and network connection.")
            return

        logging.info("Step 6: Creating audiobook...")
        audiobook_file = output_dir / f"{safe_title}_audiobook.m4b"
        try:
            create_audiobook(str(audio_dir), str(audiobook_file), str(summary_json_file))
            logging.info(f"Audiobook saved to: {audiobook_file}")
        except Exception as e:
            logging.error(f"Error creating audiobook: {e}")
            logging.exception("Error creating audiobook")

    logging.info("Processing completed.")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
