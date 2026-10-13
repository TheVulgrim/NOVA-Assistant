# NOVA

**NOVA** (*Networked Operations & Virtual Assistant*) is a Python desktop assistant that turns natural-language commands into registered skills for controlling and inspecting a computer.

The project is currently optimized for Linux, supports typed commands with spoken responses through `pyttsx3`, and includes Windows implementations for several core tasks.

## Features

- Launch supported local applications
- Capture screenshots with Flameshot on Linux or built-in PowerShell/.NET APIs on Windows
- Display CPU, memory, battery, temperature, and fan information
- Lock the screen
- Open supported websites in the default browser
- Mute, unmute, and adjust system volume on Linux or Windows
- Activate a platform-aware stealth mode
- Tell jokes and provide other small utility responses
- Use a local Ollama model for intent classification, with keyword routing as a fallback
- Launch common applications on Linux and Windows
- Lock Linux with `loginctl` or Windows with `LockWorkStation`

## New Features

- **Floating Avatar UI** – Frameless, translucent window that stays on top.  Drag‑and‑drop movement works on Wayland and X11.
- **Chat Pop‑over** – Click the avatar to toggle a sleek, glass‑morphism chat bubble with auto‑scrolling log and input field.
- **Dynamic Web Browser Skill** – accepts any URL, parses domains, and falls back to a Google search when no direct match is found.
- **Conversational Chat Engine** – dual‑mode intent routing: skill‑based actions first, then free‑form chat via Ollama.  Includes a system persona, conversation memory, and offline fallback messages.
- **Retained Async Workers** – `IntentWorker` and `VoiceInputWorker` continue to run in background threads without UI stutter.
- **Improved Drag Handling** – Uses `windowHandle().startSystemMove()` for reliable movement on Wayland.

---


## Project structure

```text
.
├── main.py                 # Application entry point
├── core/
│   ├── intent.py           # Ollama intent classification
│   ├── registry.py         # Skill registration
│   └── router.py           # Keyword-based fallback routing
├── skills/
│   └── system_skills.py    # System and utility skills
```

## Requirements

- Python 3.10+
- Linux is the primary supported platform; Windows support covers the core system skills
- Optional: Ollama running locally with the configured model
- Linux system tools used by individual skills may include `flameshot`, `pactl`, `wmctrl`, `ptyxis`, and `cmatrix`
- Windows screenshot support uses built-in PowerShell, Windows volume controls use media keys, and application launching uses native executables

Install the Python dependencies:

```bash
python -m pip install requests pyttsx3 psutil tabulate pyjokes cowsay
```

On Fedora-based Linux systems, speech and selected system skills may also need:

```bash
sudo dnf install espeak-ng flameshot pulseaudio-utils wmctrl cmatrix
```

## Running NOVA

From the project directory:

```bash
python main.py
```

Type a command such as:

```text
screenshot
system status
open calculator
open youtube
increase volume
```

Use `exit`, `quit`, or `bye` to close NOVA. Press `Ctrl+C` to stop the program safely.

## Ollama integration

`core/intent.py` sends commands to:

```text
http://localhost:11434/api/generate
```

The configured model is `llama3.2:3b`. If Ollama is unavailable or returns an invalid response, NOVA falls back to the keyword router.

To use the intent layer, install and start Ollama, then make sure the configured model is available:

```bash
ollama serve
ollama pull llama3.2:3b
```

## Safety and limitations

NOVA can start applications and execute system actions, so only run it in an environment where you trust the registered skills. Commands are limited by the functions registered in `skills/system_skills.py`; NOVA does not provide unrestricted shell access.

Some features are platform-specific. Linux screenshots rely on Flameshot and Linux stealth mode uses `wmctrl`, `ptyxis`, and `cmatrix`. Windows screenshots use PowerShell and .NET screen APIs, so no extra Python imaging package is required.

> **First run:** the first command can take 1–2 minutes while Ollama starts and loads
> `llama3.2:3b` into memory (the first `ollama pull` also downloads about 2 GB).
> Later commands are much faster. If Ollama isn't ready in time, NOVA falls back
> to keyword routing.

## Roadmap

Planned improvements include:

- More reliable volume and sensor handling
- Additional web and network skills

## Current Status

| Capability                     | Status                       |
| ------------------------------ | ---------------------------- |
| Typed commands                 | Working                      |
| Spoken responses (`pyttsx3`)   | Working                      |
| Voice commands (speech input)  | In progress, not active yet  |
| Ollama intent classification   | Working                      |
| Keyword-router fallback        | Working                      |
- Phone presence detection on the local network (Going to be added in future Updates)
- Speech-to-text input
- A more polished NOVA persona
- Expanded Windows support for more applications and system controls
