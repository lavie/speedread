import sys
import argparse
from pathlib import Path
from openai import OpenAI
import asyncio
from openai import APIError

async def text_to_speech(client, text, output_file):
    response = await asyncio.to_thread(
        client.audio.speech.create,
        model="tts-1",
        voice="alloy",
        input=text
    )
    
    await asyncio.to_thread(response.stream_to_file, output_file)

async def async_main():
    parser = argparse.ArgumentParser(description='Convert text from stdin to speech MP3.')
    parser.add_argument('output', type=str, help='Output MP3 file path')
    args = parser.parse_args()

    client = OpenAI()
    text = sys.stdin.read().strip()

    if not text:
        print("Error: No input received from stdin.", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        await text_to_speech(client, text, str(output_path))
        print(f"Audio saved to {output_path}")
    except APIError as e:
        if e.code == 'insufficient_quota':
            print("Error: You have exceeded your OpenAI API quota. Please check your plan and billing details.", file=sys.stderr)
        else:
            print(f"API Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
