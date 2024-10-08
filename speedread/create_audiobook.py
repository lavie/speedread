import os
import subprocess
import json
import argparse
import tempfile
import logging
import re
from pathlib import Path
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_duration(file_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(file_path)]
    logging.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

def clean_chapter_title(chapter_number, chapter_title):
    # Remove leading chapter numbers if present
    cleaned_title = re.sub(r'^\d+\.?\s*:?\s*', '', chapter_title).strip()
    return cleaned_title

def read_summary_file(summary_file):
    try:
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
        author = summary_data.get('author', 'Unknown Author')
        title = summary_data.get('title', 'Unknown Title')
    except Exception as e:
        logging.error(f"Error reading summary file: {e}")
        author = 'Unknown Author'
        title = 'Unknown Title'
        summary_data = {}
    return author, title, summary_data

def create_file_list(mp3_files, temp_dir_path):
    file_list_path = temp_dir_path / 'file_list.txt'
    with open(file_list_path, 'w') as f:
        for mp3_file in tqdm(mp3_files, desc="Creating file list"):
            f.write(f"file '{mp3_file.absolute()}'\n")
    return file_list_path

def combine_mp3_files(file_list_path, output_file):
    logging.info("Combining MP3 files into M4B...")
    cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(file_list_path),
           '-c:a', 'aac', '-b:a', '64k', '-f', 'mp4', str(output_file)]
    logging.info(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def create_chapter_information(mp3_files, summary_data):
    logging.info("Creating chapter information...")
    chapters = []
    current_time = 0
    for i, (mp3_file, chapter_data) in enumerate(tqdm(zip(mp3_files, summary_data['summaries']), desc="Processing chapters"), 1):
        duration = get_duration(mp3_file)
        clean_title = clean_chapter_title(i, chapter_data['chapter_title'])
        chapters.append(f"CHAPTER{i:02d}={format_time(current_time)}")
        if clean_title:
            chapters.append(f"CHAPTER{i:02d}NAME=Chapter {i}: {clean_title}")
        else:
            chapters.append(f"CHAPTER{i:02d}NAME=Chapter {i}")
        current_time += duration
    return chapters

def write_chapter_file(chapters, output_file):
    chapters_file = output_file.with_suffix('.chapters.txt')
    with open(chapters_file, 'w') as f:
        f.write('\n'.join(chapters))
    return chapters_file

def add_chapters_and_metadata(output_file, author, title):
    logging.info("Adding chapters to M4B file...")
    try:
        cmd = ['mp4chaps', '-i', str(output_file)]
        logging.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        metadata_cmd = ['mp4tags']
        metadata_cmd.extend(['-a', author])
        metadata_cmd.extend(['-s', title])
        metadata_cmd.extend(['-A', title])  # Set album name to title
        metadata_cmd.extend(['-m', author])  # Set composer to author
        metadata_cmd.extend(['-w', author])  # Set writer to author
        metadata_cmd.append(str(output_file))
        logging.info(f"Running command: {' '.join(metadata_cmd)}")
        subprocess.run(metadata_cmd, check=True)
        
        logging.info("Metadata added successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error adding chapters or metadata: {e}")
        logging.error("Error output:")
        logging.error(e.stderr)
        logging.error("Make sure mp4chaps and mp4tags are installed and in your PATH.")
        logging.error("You can try installing them with: brew install mp4v2")
        return False
    return True

def create_audiobook(input_dir, output_file, summary_file):
    input_dir = Path(input_dir)
    output_file = Path(output_file)
    mp3_files = sorted(input_dir.glob('*.mp3'))
    
    logging.info("Creating audiobook...")
    
    author, title, summary_data = read_summary_file(summary_file)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        file_list_path = create_file_list(mp3_files, temp_dir_path)
        combine_mp3_files(file_list_path, output_file)
        
        chapters = create_chapter_information(mp3_files, summary_data)
        chapters_file = write_chapter_file(chapters, output_file)
        
        success = add_chapters_and_metadata(output_file, author, title)
        
        # Clean up the chapters file
        os.remove(chapters_file)
    
    if success:
        logging.info("Audiobook creation completed!")
        logging.info(f"Audiobook file: {output_file}")
        logging.info("You can now try playing the audiobook to check if it works correctly.")
    else:
        logging.error("Audiobook creation failed.")

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

def main():
    parser = argparse.ArgumentParser(description='Create an M4B audiobook from MP3 files with chapters.')
    parser.add_argument('input_dir', help='Directory containing input MP3 files')
    parser.add_argument('output_file', help='Path for the output M4B audiobook file')
    parser.add_argument('summary_file', help='Path to the JSON summary file')
    args = parser.parse_args()

    create_audiobook(args.input_dir, args.output_file, args.summary_file)
    print(f"Audiobook created: {args.output_file}")

if __name__ == "__main__":
    main()
