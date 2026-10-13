import os
import platform
import re
import shutil
import subprocess
import tempfile
from gtts import gTTS

DEFAULT_LANG = "en"
DEFAULT_TLD = "co.uk"  # Soft, calm British accent voice
current_platform = platform.system()


def _clean_text_for_speech(text: str) -> str:
    """Prepare text for TTS by stripping terminal ASCII art and table formatting."""
    if not text:
        return ""

    text = str(text)

    # If the text is from cowsay, extract just the spoken message
    if "^__^" in text or "(__)" in text:
        bubble_matches = re.findall(r"[<|]\s*(.*?)\s*[>|]", text)
        if bubble_matches:
            return " ".join(bubble_matches)

    # If the text contains tabulate grid tables (+---+---+)
    if "+---" in text or "+===" in text:
        cleaned_rows = []
        for line in text.splitlines():
            line = line.strip()
            # Skip border divider lines like +------+------+
            if not line or re.match(r"^\+[-+=+]+\+$", line):
                continue
            # Parse table data lines: | Metric | Value |
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|") if c.strip()]
                # Skip header rows
                if len(cells) == 2 and cells[0].lower() in ["heading", "key", "metric"]:
                    continue
                if len(cells) >= 2:
                    cleaned_rows.append(f"{cells[0]}: {cells[1]}")
                elif len(cells) == 1:
                    cleaned_rows.append(cells[0])
            else:
                cleaned_rows.append(line)
        text = ". ".join(cleaned_rows)

    # Clean up excess whitespace and repeated punctuation
    text = re.sub(r"[\r\n]+", ". ", text)
    text = re.sub(r"[-_=]{3,}", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _play_audio(file_path: str):
    """Play audio file across platforms using native CLI players."""
    silent = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }

    if current_platform == "Linux":
        # 1. Prefer ffplay with a soft acoustic filter (gentle volume & warm lowpass)
        if shutil.which("ffplay"):
            try:
                subprocess.run(
                    [
                        "ffplay",
                        "-nodisp",
                        "-autoexit",
                        "-loglevel",
                        "quiet",
                        "-af",
                        "volume=0.85,lowpass=f=4500",
                        file_path,
                    ],
                    check=True,
                    **silent,
                )
                return
            except subprocess.CalledProcessError:
                # Fallback to plain ffplay if audio filters fail
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
                    **silent,
                )
                return

        # 2. Fallback to mpv
        if shutil.which("mpv"):
            subprocess.run(["mpv", "--no-terminal", file_path], **silent)
            return

        # 3. Fallback to mpg123
        if shutil.which("mpg123"):
            subprocess.run(["mpg123", "-q", file_path], **silent)
            return

    elif current_platform == "Windows":
        # Play via PowerShell MediaPlayer (supports MP3)
        escaped_path = file_path.replace("'", "''")
        ps_cmd = (
            f"Add-Type -AssemblyName presentationCore; "
            f"$player = New-Object System.Windows.Media.MediaPlayer; "
            f"$player.Open([System.Uri]'{escaped_path}'); "
            f"$player.Volume = 0.85; "
            f"$player.Play(); "
            f"Start-Sleep -Milliseconds 1200; "
            f"while ($player.Position -lt $player.NaturalDuration.TimeSpan) {{ Start-Sleep -Milliseconds 250 }}"
        )
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            **silent,
        )

    elif current_platform == "Darwin":
        # macOS native player
        subprocess.run(["afplay", "-v", "0.85", file_path], **silent)


def speak(text: str, lang: str = DEFAULT_LANG, tld: str = DEFAULT_TLD, slow: bool = False):
    """
    Synthesize and play speech using Google Text-to-Speech (gTTS).
    
    Default configuration uses British English (tld='co.uk') and a warm audio filter
    to produce a calm, soft voice profile.
    """
    clean_text = _clean_text_for_speech(text)
    if not clean_text:
        return

    temp_path = None
    try:
        tts = gTTS(text=clean_text, lang=lang, tld=tld, slow=slow)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            temp_path = fp.name

        tts.save(temp_path)
        _play_audio(temp_path)

    except Exception as e:
        # Gracefully handle network issues or missing audio devices without crashing NOVA
        print(f"[Speech error: {str(e)}]")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

