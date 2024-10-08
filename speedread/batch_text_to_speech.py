import argparse
import asyncio
import json
import logging
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from speedread.text_to_speech import text_to_speech

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def process_chapter(client, chapter, output_dir, semaphore, voice):
    try:
        chapter_number = str(chapter.get('number', 0)).zfill(2)
        output_file = output_dir / f"chapter_{chapter_number}.mp3"
        
        logging.info(f"Processing chapter: {chapter.get('chapter_title', f'Chapter {chapter_number}')}")
        logging.info(f"Output file: {output_file}")

        if output_file.exists():
            logging.info(f"Audio file already exists: {output_file}")
            return output_file

        async with semaphore:
            max_retries = 5
            retry_delay = 10
            for attempt in range(max_retries):
                try:
                    await text_to_speech(client, chapter['summary'], str(output_file), voice)
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logging.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
        
        if output_file.exists():
            logging.info(f"Successfully generated audio file: {output_file}")
            return output_file
        else:
            logging.error(f"Failed to generate audio file: {output_file}")
            return None
    except Exception as e:
        logging.error(f"Error processing chapter {chapter_number}: {str(e)}")
        return None

async def async_main(args):
    with open(args.input_json, 'r') as f:
        book_data = json.load(f)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    semaphore = asyncio.Semaphore(args.max_concurrency)
    tasks = []

    for i, chapter in enumerate(book_data['summaries'], start=1):
        chapter['number'] = i  # Add chapter number
        task = asyncio.create_task(process_chapter(client, chapter, output_dir, semaphore, args.voice))
        tasks.append(task)

    results = []
    for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing chapters"):
        result = await task
        if result:
            results.append(result)

    print(f"Processed {len(results)} chapters. Audio files saved in {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Batch convert book chapters to speech using OpenAI API.')
    parser.add_argument('input_json', help='JSON file containing book content')
    parser.add_argument('output_dir', help='Directory to save output MP3 files')
    parser.add_argument('--max-concurrency', type=int, default=5, help='Maximum number of concurrent conversions')
    parser.add_argument('--voice', type=str, choices=VALID_VOICES, default="alloy",
                        help='Voice to use for text-to-speech (default: alloy)')
    args = parser.parse_args()

    asyncio.run(async_main(args))

if __name__ == "__main__":
    main()
