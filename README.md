# Document to Speech Converter

A simple application that converts text documents (TXT, DOCX, PDF) to speech using OpenAI's text-to-speech API.

## Features

- Support for multiple document formats (TXT, DOCX, PDF)
- OpenAI TTS voice selection (alloy, echo, fable, onyx, nova, shimmer)
- Adjustable speech speed
- Audio playback controls
- Save audio as MP3

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the same directory as the script and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Run the application:
```bash
python document_to_speech.py
```

2. Click "Browse" to select a document (TXT, DOCX, or PDF)

3. Select a voice from the dropdown menu

4. Adjust the speech speed using the slider

5. Click "Convert to Speech" to convert the document to speech

6. Use the "Stop" button to stop playback

7. Click "Save Audio" to save the generated audio as an MP3 file

## Notes

- The application has a 4096 character limit for text-to-speech conversion
- Audio files are temporarily stored in an "audio_output" directory
- Make sure you have a valid OpenAI API key with access to the TTS API 