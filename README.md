# Granny — Local Voice Assistant

Granny is a small Windows voice assistant assembled from local components. The current script uses Faster-Whisper for speech-to-text, an Ollama-hosted Granite model for intent planning and conversation, and Piper for spoken replies.

## Features

- Record speech from a selected microphone and transcribe it with Faster-Whisper.
- Ask a local Granite model to return a structured JSON action plan.
- Save and read notes and to-do items.
- Open Notepad, Calculator, File Explorer and Task Manager after asking for confirmation.
- Search file names in the home folder, Desktop, Documents or Downloads.
- Open websites after asking for confirmation.
- Speak replies with a local Piper voice.

## Important: this is a local prototype

The code below is the supplied working project snapshot, not a polished installer. Hardware, Python package and audio-device settings vary by machine. It has not been tested on a clean computer as part of this upload.

## Requirements

- Windows 10/11
- Python (a compatible version for all audio/ML dependencies; Python 3.11 or 3.12 is a sensible starting point)
- [Ollama](https://ollama.com/) with the `granite4:3b` model available locally
- A microphone and speakers/headphones
- Piper TTS and the UK Alan medium voice model

## Setup outline

1. Install Python and Ollama.
2. Open Command Prompt and download the model:

   ```powershell
   ollama pull granite4:3b
   ```

3. Install the Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Install Piper TTS and place the `en_GB-alan-medium.onnx` voice file at:

   ```text
   %USERPROFILE%\piper-voices\en_GB-alan-medium.onnx
   ```

   Make sure the matching Piper voice metadata file is present too if your Piper distribution requires it.

5. Check the microphone index in the script. The current value is `MIC_DEVICE = 1`; it may need changing on another PC.
6. Run:

   ```powershell
   python granite_task_assistant.py
   ```

The first Faster-Whisper run may download its model files. Ollama must be running locally at `http://localhost:11434`.

## Data and local permissions

Notes and to-dos are stored in `%USERPROFILE%\GrannyAssistant\notes.txt` and `todos.txt`. Temporary recording and reply WAV files are stored in the user profile folder.

The file-search feature walks file names beneath the selected folder and can return local paths. The assistant can launch the four listed Windows apps and open web URLs. App and website actions ask for confirmation, but file searching is performed directly. Review the code before running it, especially if you adapt the allowed actions or run a model you do not trust.

The code does not intentionally send recordings to a hosted AI API: speech recognition runs through Faster-Whisper locally, and prompts are sent to the local Ollama endpoint. Package/model downloads still require internet access during setup.

## Known limitations

- Speech recognition can confuse similar-sounding words, such as “buy” and “by”. The current code includes one narrow correction attempt, but it is not a general solution to transcription errors. Always check saved items.
- The current implementation appends directly to the to-do and notes files. It does not ask for confirmation before saving every interpreted task.
- “Last item” recall is held in memory only and resets when the script restarts.
- Microphone selection is hard-coded to device index 1.
- Some imports are redundant, and the project would benefit from broader error handling and automated tests.

## Troubleshooting

- **Ollama connection error:** check that Ollama is running and that `ollama list` shows `granite4:3b`.
- **Voice model not found:** check the exact path to `en_GB-alan-medium.onnx`.
- **No audio / wrong microphone:** inspect available devices with a short `sounddevice` device-listing script and update `MIC_DEVICE`.
- **Dependency installation fails:** try Python 3.11 or 3.12 in a fresh virtual environment and follow the install guidance for Faster-Whisper, sounddevice and Piper on Windows.

## Files

- `granite_task_assistant.py` — the current supplied application script.
- `requirements.txt` — Python package dependencies.
- `.gitignore` — excludes local recordings, voice models, and user data from version control.

## Current project status

The assistant was confirmed working on the developer's Windows PC on 26 October 2026. The repository upload is a snapshot for learning and reproduction; it is not a guarantee of plug-and-play operation on another system.
