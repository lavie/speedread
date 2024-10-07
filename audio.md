# Audio Conversion Plan

## Objective
Convert chapter summaries to MP3 files using the OpenAI Audio API.

## Steps

### 1. Environment Setup
- [x] Ensure OpenAI Python library is installed and up-to-date
- [x] Set up OpenAI API key as an environment variable

### 2. Create Python Script
- [ ] Create `text_to_speech.py` in the `speedread` directory
- [ ] Import necessary libraries (OpenAI, os, argparse, asyncio, tqdm)
- [ ] Set up argument parsing for input and output directories

### 3. Implement Main Functionality
- [ ] Function to read text files from input directory
- [ ] Function to convert text to speech using OpenAI's Text-to-Speech API
- [ ] Function to save audio output as MP3 files
- [ ] Implement asyncio for concurrent processing

### 4. Error Handling and Logging
- [ ] Implement try-except blocks for API calls and file operations
- [ ] Add progress tracking using tqdm

### 5. Optimize for Efficiency
- [ ] Process files in parallel using asyncio
- [ ] Implement rate limiting using asyncio.Semaphore

### 6. Update Poetry Configuration
- [ ] Add new script to `pyproject.toml`

### 7. Testing
- [ ] Run script on a small set of summary files
- [ ] Verify quality and correctness of output

### 8. Documentation
- [ ] Update README.md with usage instructions for the new feature

## Next Steps
- Implement the plan in `text_to_speech.py`
- Update `pyproject.toml`
- Update README.md with new feature details
- Conduct thorough testing
- Integrate with existing workflow
