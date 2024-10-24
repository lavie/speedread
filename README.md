# SpeedRead Tools

SpeedRead Tools is a Python-based project that processes EPUB books to create summaries and audiobooks using AI. It leverages OpenAI's GPT model for summarization and text-to-speech conversion.

## Features

- Convert EPUB files to structured text
- Summarize book content using GPT-4
- Generate HTML summaries with a clean, readable layout
- Create audiobooks from summaries
- Customizable dark/light/medium mode for HTML summaries

## Requirements

- Python 3.8+
- Poetry (for dependency management)
- OpenAI API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/lavie/speedread.git
   cd speedread
   ```

2. Install dependencies using Poetry:
   ```
   poetry install
   ```

3. Set up your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY='your-api-key-here'
   ```

## Usage

### Using Poetry

The main CLI script `speedread_cli.py` combines all the functionality into a single command. Here's how to use it:

```
poetry run speedread <epub_file> [options]
```

Arguments:
- `<epub_file>`: Path to the input EPUB file (required)

Options:
- `--audiobook`: Create an audiobook from the summaries
- `--concurrency <num>`: Set the number of concurrent operations (default: 5)
- `--voice <voice>`: Specify the voice for text-to-speech (default: "alloy")
  Available voices: alloy, echo, fable, nova, onyx, shimmer
- `-y, --yes`: Skip confirmation prompts
- `--help`: Show help message and exit

Examples:
```bash
# Basic usage - creates summary only
poetry run speedread my_ebook.epub

# Create summary and audiobook with default settings
poetry run speedread my_ebook.epub --audiobook

# Create audiobook with specific voice and higher concurrency
poetry run speedread my_ebook.epub --audiobook --voice nova --concurrency 8

# Skip all confirmation prompts
poetry run speedread my_ebook.epub --audiobook -y
```

### Using Docker

To run the project using Docker, first build the Docker image (see the "Building the Docker Image" section below), then use the following command:

```
docker run -v $(pwd):/data -e OPENAI_API_KEY='your-api-key-here' assaflavie/speedread /data/my_ebook.epub [options]
```

You can use this free epub as an example: https://www.epubbooks.com/book/335-decline-and-fall-of-the-roman-empire-volume-1

Replace `'your-api-key-here'` with your actual OpenAI API key.

This command will:
1. Parse the EPUB file
2. Trim chapters to focus on main content
3. Summarize the book using GPT-4
4. Create an HTML summary
5. Generate an audiobook (if `--audiobook` flag is used)

The output files will be saved in a directory named after the book title in the same location as the input EPUB file.

## Building the Docker Image

To build the Docker image for this project:

1. Ensure you have Docker installed on your system.
2. Navigate to the project root directory in your terminal.
3. Run the following command:

```
make docker-build
```

This command uses the Makefile to build the Docker image with the tag `assaflavie/speedread`.

After building the image, you can run the project using the Docker command provided in the "Using Docker" section above.

## Output

- A JSON file containing the book summary
- An HTML file with the formatted summary (with dark/light/medium mode toggle)
- MP3 audio files for each chapter (if audiobook option is selected)
- An M4B audiobook file (if audiobook option is selected) which you can import into your Books app on iOS for example.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
