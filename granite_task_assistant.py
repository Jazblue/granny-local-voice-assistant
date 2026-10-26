from pathlib import Path
import json
import sounddevice
import shutil
import subprocess
import urllib.request
import webbrowser
from scipy.io import wavfile
import os

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write, read
from faster_whisper import WhisperModel

BASE = Path.home()
DATA = BASE / "GrannyAssistant"
DATA.mkdir(exist_ok=True)
NOTES = DATA / "notes.txt"
TODOS = DATA / "todos.txt"

VOICE = BASE / "piper-voices" / "en_GB-alan-medium.onnx"
RECORDING = BASE / "granite-live-recording.wav"
REPLY_WAV = BASE / "granite-live-reply.wav"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "granite4:3b"
SAMPLE_RATE = 16000
MIC_DEVICE = 1

LAST_PATH = None
LAST_TEXT = ""

APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "file explorer": ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
}



def speak(text):
    if not VOICE.exists():
        print(f"Voice model not found: {VOICE}")
        print("Reply shown as text.")
        return

    try:
        subprocess.run(
            [
                "python", "-m", "piper",
                "-m", str(VOICE),
                "-f", str(REPLY_WAV),
            ],
            input=text,
            text=True,
            check=True,
            capture_output=True,
        )

        if REPLY_WAV.exists():
            sample_rate, audio = wavfile.read(str(REPLY_WAV))
            import numpy as np
            audio = audio.astype(np.float32)
            audio = audio / max(float(abs(audio).max()), 1.0)
            sounddevice.play(audio, sample_rate)
            sounddevice.wait()
        else:
            print("Piper did not create an audio file.")

    except Exception as e:
        print(f"Voice playback failed: {e}")
        print("Reply shown as text.")



def save_item(path, text):
    global LAST_PATH, LAST_TEXT
    text = str(text).strip().replace("\x00", "")
    if not text:
        return "I didn't catch what you want me to save."
    with path.open("a", encoding="utf-8") as f:
        f.write(text.replace("\n", " ") + "\n")
    LAST_PATH = path
    LAST_TEXT = text
    return f"Done! I've saved that in {path}. Would you like me to read it back?"


def read_file(path, label):
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return f"You haven't saved any {label} yet."
    return f"Here are your {label}: {path.read_text(encoding='utf-8')[-2500:]}"


def confirm(question):
    return input(f"{question} (y/N): ").strip().lower() in ("y", "yes")


def get_plan(text):
    prompt = f"""
You are Granny, a witty British assistant. Return only JSON with keys
action and args. Allowed actions:
add_note: args text
read_notes: empty args
add_todo: args task
read_todos: empty args
open_app: args app (notepad, calculator, file explorer, task manager)
search_files: args query and folder (home, desktop, documents, downloads)
open_website: args url
chat: args reply
Never invent actions. If unsure, use chat.
User said: {text}
"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        result = json.loads(response.read().decode())
    return json.loads(result["response"])


def search_files(query, folder):
    folders = {
        "home": BASE,
        "desktop": BASE / "Desktop",
        "documents": BASE / "Documents",
        "downloads": BASE / "Downloads",
    }
    root = folders.get(str(folder).lower(), BASE)
    query = str(query).lower().strip()
    matches = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {
            "AppData", ".git", "node_modules", "__pycache__"
        }]
        for name in files:
            if query and query in name.lower():
                matches.append(str(Path(current) / name))
                if len(matches) >= 20:
                    break
        if len(matches) >= 20:
            break
    return ("Found: " + "; ".join(matches)) if matches else f"No matching files found in {root}."


def execute(plan):
    action = plan.get("action", "chat")
    args = plan.get("args", {})
    if not isinstance(args, dict):
        args = {}

    if action == "add_note":
        return save_item(NOTES, args.get("text", ""))
    if action == "read_notes":
        return read_file(NOTES, "notes")
    if action == "add_todo":
        return save_item(TODOS, args.get("task", ""))
    if action == "read_todos":
        return read_file(TODOS, "to-do items")
    if action == "open_app":
        app = str(args.get("app", "")).lower()
        if app not in APPS:
            return "I can open Notepad, Calculator, File Explorer or Task Manager."
        if confirm(f"Open {app}?"):
            subprocess.Popen(APPS[app], shell=False)
            return f"Opening {app}."
        return "No problem, I haven't opened it."
    if action == "search_files":
        return search_files(args.get("query", ""), args.get("folder", "home"))
    if action == "open_website":
        url = str(args.get("url", "")).strip()
        if not url.startswith(("https://", "http://")):
            url = "https://" + url
        if not url.startswith(("https://", "http://")) or not confirm(f"Open {url}?"):
            return "I haven't opened that website."
        webbrowser.open(url)
        return f"Opening {url}."
    if action == "chat":
        return str(args.get("reply", "I'm listening. What would you like?"))
    return "I don't know how to do that yet."



def follow_up(text):
    lower = text.lower().strip()
    
	

    # Read back the to-do list.
    if any(p in lower for p in (
        "read back", "read my tasks", "read my to-do",
        "read my todo", "read the task list", "read my list",
        "what are my tasks", "what's on my list",
        "what is on my list"
    )):
        return read_file(TODOS, "to-do items")

    # Repeat the last item saved.
    if any(p in lower for p in (
        "read it back", "read that back", "read it out",
        "what did you save", "what did you write",
        "what did you just save",
    )):
        if LAST_PATH and LAST_TEXT:
            return f"Of course! You asked me to save: {LAST_TEXT}. It's stored in {LAST_PATH}."
        return "I don't have the last saved item in memory. Your notes are in " + str(NOTES) + " and your to-do list is in " + str(TODOS) + "."

    # Tell me where items were saved.
    if any(p in lower for p in (
        "where did you save", "where is it saved", "where did you put",
        "where are my notes saved", "where are my tasks saved",
    )):
        if LAST_PATH:
            return f"Your last saved item is in {LAST_PATH}. The text was: {LAST_TEXT}"
        return f"Your notes are in {NOTES}, and your to-do list is in {TODOS}."

    return None



def record():
    input("\nPress Enter to start speaking...")
    print("Recording... speak naturally, then press Enter to stop.")
    chunks = []

    def callback(indata, frames, time_info, status):
        chunks.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16",
        device=MIC_DEVICE, callback=callback
    ):
        input()
    if not chunks:
        raise RuntimeError("No audio recorded.")
    audio = np.concatenate(chunks, axis=0)
    write(str(RECORDING), SAMPLE_RATE, audio)
    return str(RECORDING)


def main():
    print("Loading Whisper...")
    whisper = WhisperModel("base", device="cpu", compute_type="int8")
    print("Granny is ready. Say 'stop assistant' to quit.")

    while True:
        try:
            audio_file = record()
            print("Transcribing...")
            segments, _ = whisper.transcribe(audio_file, language="en")
            text = " ".join(s.text.strip() for s in segments).strip()
            if not text:
                print("I didn't catch that.")
                continue

           
            print("You said:", text)
            lower = text.lower().strip()

            # Correct this common Whisper mishearing.
            if lower.startswith("add a task by "):
                text = "Add a task, buy " + text[len("add a task by "):].strip()
                lower = text.lower().strip()

            if "stop assistant" in lower:
                speak("Right then, Jase. I'll leave you in peace. See you later!")
                break

            # Direct task commands: bypass Granite for simple to-dos.
            task_prefixes = [
                "add a to-do", "add to-do", "add a todo", "add todo",
                "add a task", "add task", "remind me to",
                "i need to", "i have to do", "i had to do"
            ]

            task_text = None
            for prefix in task_prefixes:
                if lower.startswith(prefix):
                    task_text = text[len(prefix):].strip(" .,:;-")
                    break

            if task_text:
                reply = save_item(TODOS, task_text)
            else:
                reply = follow_up(text)
                if reply is None:
                    print("Granite is thinking...")
                    try:
                        plan = get_plan(text)
                        print("Selected action:", plan.get("action", "unknown"))
                        reply = execute(plan)
                    except Exception as error:
                        print("Assistant error:", error)
                        reply = "Sorry, something went wrong. I haven't completed that task."

            print("Granny:", reply)
            speak(reply)

        except KeyboardInterrupt:
            print("\nStopping Granny.")
            break
        except Exception as error:
            print("Assistant error:", error)
            print("Check the microphone and try again.")

    print("Granny has stopped.")


if __name__ == "__main__":
    main()
