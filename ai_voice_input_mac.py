#!/usr/bin/env python3
"""
AI Voice Input for macOS
Voice-to-text input powered by OpenAI Whisper API.
Press a hotkey — speak — text gets pasted into any active window.

macOS port of the original Windows AutoHotkey script.
"""

import configparser
import os
import subprocess
import sys
import tempfile
import threading
import time

import requests
import sounddevice as sd
import soundfile as sf
from pynput import keyboard


# ---------------------------------------------------------------------------
#  Globals
# ---------------------------------------------------------------------------
is_recording = False
is_transcribing = False
is_cancelled = False
record_start_time = 0.0
audio_frames = []
audio_stream = None
recording_lock = threading.Lock()
tooltip_timer = None

WAV_FILE = os.path.join(tempfile.gettempdir(), "voice_input_recording.wav")
SAMPLE_RATE = 16000  # Whisper optimal
CHANNELS = 1

# Config values (populated by load_config)
config = {}


# ---------------------------------------------------------------------------
#  Config
# ---------------------------------------------------------------------------
def find_config_path():
    """Find config.ini next to the script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "config.ini")


def load_config():
    global config
    path = find_config_path()
    cp = configparser.ConfigParser()
    cp.read(path, encoding="utf-8")

    section = "Whisper"
    config = {
        "api_key": cp.get(section, "ApiKey", fallback=""),
        "model": cp.get(section, "Model", fallback="whisper-1"),
        "prompt": cp.get(section, "Prompt", fallback=""),
        "sound_start": cp.get(section, "SoundStart", fallback=""),
        "sound_stop": cp.get(section, "SoundStop", fallback=""),
        "sound_cancel": cp.get(section, "SoundCancel", fallback=""),
        "min_record_ms": int(cp.get(section, "MinRecordMs", fallback="1500")),
        "proxy": cp.get(section, "Proxy", fallback=""),
        "record_key": cp.get(section, "RecordKey", fallback="f9"),
    }

    api_key = config["api_key"]
    if not api_key or api_key == "sk-YOUR-API-KEY-HERE":
        show_notification("Voice Input - Error",
                          f"Set your OpenAI API key in:\n{path}")
        sys.exit(1)


# ---------------------------------------------------------------------------
#  macOS helpers
# ---------------------------------------------------------------------------
def show_notification(title, text):
    """Show macOS notification via osascript."""
    # Escape double quotes for AppleScript
    title_escaped = title.replace('"', '\\"')
    text_escaped = text.replace('"', '\\"')
    script = (
        f'display notification "{text_escaped}" '
        f'with title "{title_escaped}"'
    )
    subprocess.Popen(["osascript", "-e", script],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def play_sound(path):
    """Play a sound file using macOS afplay."""
    if path and os.path.isfile(path):
        subprocess.Popen(["afplay", path],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def play_system_sound(name):
    """Play a built-in macOS system sound by name."""
    sound_path = f"/System/Library/Sounds/{name}.aiff"
    if os.path.isfile(sound_path):
        subprocess.Popen(["afplay", sound_path],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_clipboard():
    """Get current clipboard contents."""
    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True,
                                timeout=2)
        return result.stdout
    except Exception:
        return ""


def set_clipboard(text):
    """Set clipboard contents."""
    try:
        subprocess.run(["pbcopy"], input=text, text=True, timeout=2)
    except Exception:
        pass


def paste_text():
    """Simulate Cmd+V paste in the active application via AppleScript."""
    script = '''
    tell application "System Events"
        keystroke "v" using command down
    end tell
    '''
    subprocess.run(["osascript", "-e", script],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=5)


def send_enter():
    """Simulate Enter key press via AppleScript."""
    script = '''
    tell application "System Events"
        key code 36
    end tell
    '''
    subprocess.run(["osascript", "-e", script],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=5)


# ---------------------------------------------------------------------------
#  Recording timer display
# ---------------------------------------------------------------------------
def update_recording_tooltip():
    """Periodically show recording duration notification."""
    global tooltip_timer, is_recording, record_start_time
    if not is_recording:
        return
    elapsed = time.time() - record_start_time
    secs = int(elapsed)
    mins = secs // 60
    s = secs % 60
    if mins > 0:
        time_str = f"{mins}:{s:02d}"
    else:
        time_str = f"{secs}s"
    # Print to terminal (tooltip equivalent)
    print(f"\r🎙 Recording... {time_str}  (RecordKey/Esc)", end="", flush=True)
    # Schedule next update
    tooltip_timer = threading.Timer(1.0, update_recording_tooltip)
    tooltip_timer.daemon = True
    tooltip_timer.start()


# ---------------------------------------------------------------------------
#  Audio recording
# ---------------------------------------------------------------------------
def audio_callback(indata, frames, time_info, status):
    """Called by sounddevice for each audio block."""
    global audio_frames
    if status:
        print(f"\n⚠ Audio status: {status}", flush=True)
    audio_frames.append(indata.copy())


def start_recording():
    """Start capturing audio from microphone."""
    global is_recording, audio_frames, audio_stream, record_start_time
    global tooltip_timer

    with recording_lock:
        if is_recording:
            return
        is_recording = True

    # Delete old file
    if os.path.exists(WAV_FILE):
        try:
            os.remove(WAV_FILE)
        except OSError:
            pass

    audio_frames = []

    try:
        audio_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=audio_callback,
        )
        audio_stream.start()
    except Exception as e:
        print(f"\n❌ Microphone error: {e}", flush=True)
        show_notification("Voice Input - Error", f"Microphone error: {e}")
        with recording_lock:
            is_recording = False
        return

    play_sound(config["sound_start"])
    if not config["sound_start"]:
        play_system_sound("Tink")

    record_start_time = time.time()
    print(flush=True)
    update_recording_tooltip()


def stop_recording():
    """Stop capturing and save WAV file. Returns True if file saved ok."""
    global is_recording, audio_stream, tooltip_timer

    with recording_lock:
        if not is_recording:
            return False
        is_recording = False

    # Stop timer
    if tooltip_timer:
        tooltip_timer.cancel()
        tooltip_timer = None

    # Stop stream
    if audio_stream:
        try:
            audio_stream.stop()
            audio_stream.close()
        except Exception:
            pass
        audio_stream = None

    if not audio_frames:
        print("\n❌ No audio captured", flush=True)
        return False

    # Save WAV
    import numpy as np
    try:
        data = np.concatenate(audio_frames, axis=0)
        sf.write(WAV_FILE, data, SAMPLE_RATE, subtype="PCM_16")
    except Exception as e:
        print(f"\n❌ WAV save error: {e}", flush=True)
        return False

    # Validate
    if not os.path.exists(WAV_FILE):
        print("\n❌ WAV file not created", flush=True)
        return False

    file_size = os.path.getsize(WAV_FILE)
    if file_size < 1000:
        print(f"\n❌ WAV too small ({file_size} bytes). Microphone not recording.", flush=True)
        return False

    return True


def cancel_recording():
    """Cancel recording without transcription."""
    global is_recording, audio_stream, tooltip_timer

    with recording_lock:
        if not is_recording:
            return
        is_recording = False

    if tooltip_timer:
        tooltip_timer.cancel()
        tooltip_timer = None

    if audio_stream:
        try:
            audio_stream.stop()
            audio_stream.close()
        except Exception:
            pass
        audio_stream = None

    if os.path.exists(WAV_FILE):
        try:
            os.remove(WAV_FILE)
        except OSError:
            pass

    play_sound(config["sound_cancel"])
    if not config["sound_cancel"]:
        play_system_sound("Basso")

    print("\n❌ Cancelled", flush=True)


# ---------------------------------------------------------------------------
#  Whisper API
# ---------------------------------------------------------------------------
def whisper_transcribe(file_path):
    """Send audio to OpenAI Whisper API and return transcribed text."""
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
    }
    data = {
        "model": config["model"],
        "response_format": "text",
    }
    if config["prompt"]:
        data["prompt"] = config["prompt"]

    proxies = {}
    if config["proxy"]:
        proxies = {
            "http": config["proxy"],
            "https": config["proxy"],
        }

    try:
        with open(file_path, "rb") as f:
            files = {"file": ("recording.wav", f, "audio/wav")}
            response = requests.post(
                url,
                headers=headers,
                data=data,
                files=files,
                proxies=proxies,
                timeout=30,
            )
        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"\n❌ API error {response.status_code}: {response.text[:200]}", flush=True)
            return ""
    except requests.exceptions.Timeout:
        print("\n❌ API timeout (30s)", flush=True)
        return ""
    except Exception as e:
        print(f"\n❌ API error: {e}", flush=True)
        return ""


# ---------------------------------------------------------------------------
#  Stop & Transcribe
# ---------------------------------------------------------------------------
def stop_and_transcribe(auto_enter=False):
    """Stop recording, send to API, paste result."""
    global is_transcribing, is_cancelled

    print("\r⏳ Recognizing... (Esc to cancel)       ", flush=True)

    if not stop_recording():
        return

    # Check minimum duration
    elapsed_ms = (time.time() - record_start_time) * 1000
    if config["min_record_ms"] > 0 and elapsed_ms < config["min_record_ms"]:
        if os.path.exists(WAV_FILE):
            try:
                os.remove(WAV_FILE)
            except OSError:
                pass
        play_sound(config["sound_cancel"])
        if not config["sound_cancel"]:
            play_system_sound("Basso")
        print("\n❌ Cancelled (too short)", flush=True)
        return

    # Play stop sound
    play_sound(config["sound_stop"])
    if not config["sound_stop"]:
        play_system_sound("Pop")

    # Transcribe
    is_cancelled = False
    is_transcribing = True
    text = whisper_transcribe(WAV_FILE)
    is_transcribing = False

    # Clean up WAV
    if os.path.exists(WAV_FILE):
        try:
            os.remove(WAV_FILE)
        except OSError:
            pass

    # Check cancellation
    if is_cancelled:
        print("\n❌ Cancelled", flush=True)
        show_notification("Voice Input", "Cancelled")
        return

    # Check empty
    if not text or not text.strip():
        print("\n❌ Nothing recognized", flush=True)
        show_notification("Voice Input", "Nothing recognized")
        return

    # Paste text
    prev_clip = get_clipboard()
    set_clipboard(text)
    time.sleep(0.05)
    paste_text()
    time.sleep(0.1)
    set_clipboard(prev_clip)

    if auto_enter:
        time.sleep(0.05)
        send_enter()

    preview = text[:60] + ("..." if len(text) > 60 else "")
    print(f"\n✓ {preview}", flush=True)
    show_notification("Voice Input", f"✓ {preview}")


# ---------------------------------------------------------------------------
#  Toggle recording
# ---------------------------------------------------------------------------
def toggle_recording():
    """Toggle recording on/off (called by hotkey)."""
    if is_recording:
        threading.Thread(target=stop_and_transcribe, args=(False,), daemon=True).start()
    else:
        start_recording()


# ---------------------------------------------------------------------------
#  Hotkey parsing
# ---------------------------------------------------------------------------
SPECIAL_KEYS = {
    "f1": keyboard.Key.f1, "f2": keyboard.Key.f2, "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4, "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7, "f8": keyboard.Key.f8, "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10, "f11": keyboard.Key.f11, "f12": keyboard.Key.f12,
    "f13": keyboard.Key.f13, "f14": keyboard.Key.f14, "f15": keyboard.Key.f15,
    "f16": keyboard.Key.f16, "f17": keyboard.Key.f17, "f18": keyboard.Key.f18,
    "f19": keyboard.Key.f19, "f20": keyboard.Key.f20,
    "home": keyboard.Key.home, "end": keyboard.Key.end,
    "pageup": keyboard.Key.page_up, "pagedown": keyboard.Key.page_down,
    "insert": keyboard.Key.insert, "delete": keyboard.Key.delete,
    "scrolllock": keyboard.Key.scroll_lock,
    "pause": keyboard.Key.pause,
    "numlock": keyboard.Key.num_lock,
    "capslock": keyboard.Key.caps_lock,
    "printscreen": keyboard.Key.print_screen,
    "right": keyboard.Key.right, "left": keyboard.Key.left,
    "up": keyboard.Key.up, "down": keyboard.Key.down,
}

MODIFIER_MAP = {
    "ctrl": keyboard.Key.ctrl_l,
    "cmd": keyboard.Key.cmd,
    "alt": keyboard.Key.alt_l,
    "shift": keyboard.Key.shift_l,
    "option": keyboard.Key.alt_l,
}


def parse_hotkey(key_string):
    """
    Parse hotkey string into (modifiers_set, trigger_key).

    Formats:
        f9           -> no modifiers, F9 key
        ctrl+f9      -> ctrl modifier, F9 key
        cmd+shift+f9 -> cmd+shift modifiers, F9 key
    """
    parts = key_string.lower().strip().split("+")
    modifiers = set()
    trigger = None

    for part in parts:
        part = part.strip()
        if part in MODIFIER_MAP:
            modifiers.add(MODIFIER_MAP[part])
        elif part in SPECIAL_KEYS:
            trigger = SPECIAL_KEYS[part]
        elif len(part) == 1:
            trigger = keyboard.KeyCode.from_char(part)
        else:
            print(f"⚠ Unknown key: '{part}', falling back to F9", flush=True)
            trigger = keyboard.Key.f9

    if trigger is None:
        trigger = keyboard.Key.f9

    return modifiers, trigger


# ---------------------------------------------------------------------------
#  Keyboard listener
# ---------------------------------------------------------------------------
class HotkeyListener:
    def __init__(self, record_key_str):
        self.required_modifiers, self.trigger_key = parse_hotkey(record_key_str)
        self.pressed_modifiers = set()
        self.listener = None

    def _normalize_key(self, key):
        """Normalize key for comparison (e.g., ctrl_r -> ctrl_l)."""
        mapping = {
            keyboard.Key.ctrl_r: keyboard.Key.ctrl_l,
            keyboard.Key.alt_r: keyboard.Key.alt_l,
            keyboard.Key.shift_r: keyboard.Key.shift_l,
            keyboard.Key.cmd_r: keyboard.Key.cmd,
        }
        return mapping.get(key, key)

    def on_press(self, key):
        normalized = self._normalize_key(key)

        # Track modifiers
        all_modifiers = set(MODIFIER_MAP.values())
        if normalized in all_modifiers:
            self.pressed_modifiers.add(normalized)

        # Check trigger key
        if self._key_matches(key, self.trigger_key):
            if self.required_modifiers <= self.pressed_modifiers:
                toggle_recording()
                return

        # Escape handling
        if key == keyboard.Key.esc:
            if is_transcribing:
                global is_cancelled
                is_cancelled = True
                play_sound(config["sound_cancel"])
                if not config["sound_cancel"]:
                    play_system_sound("Basso")
                print("\n❌ Cancelling...", flush=True)
            elif is_recording:
                cancel_recording()

        # Enter during recording -> stop and auto-enter
        if key == keyboard.Key.enter and is_recording:
            threading.Thread(target=stop_and_transcribe, args=(True,),
                             daemon=True).start()

    def on_release(self, key):
        normalized = self._normalize_key(key)
        self.pressed_modifiers.discard(normalized)

    def _key_matches(self, pressed, target):
        """Check if pressed key matches target key."""
        if pressed == target:
            return True
        # Handle KeyCode comparison
        if hasattr(pressed, "vk") and hasattr(target, "vk"):
            return pressed.vk == target.vk
        if hasattr(pressed, "char") and hasattr(target, "char"):
            return pressed.char == target.char
        return False

    def start(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
        )
        self.listener.start()
        return self.listener


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------
def main():
    load_config()

    record_key = config["record_key"]
    print("=" * 50)
    print("  🎙 AI Voice Input for macOS")
    print("=" * 50)
    print(f"  Hotkey:  {record_key}")
    print(f"  Model:   {config['model']}")
    print(f"  Proxy:   {config['proxy'] or 'none'}")
    print(f"  MinMs:   {config['min_record_ms']}")
    print("=" * 50)
    print(f"  {record_key} — start/stop recording")
    print("  Enter (while recording) — stop + transcribe + Enter")
    print("  Escape (while recording) — cancel")
    print("  Escape (while transcribing) — cancel")
    print("  Ctrl+C — quit")
    print("=" * 50)
    print()

    # Note about macOS permissions
    print("⚠  macOS requires Accessibility permissions for this app.")
    print("   System Preferences → Privacy & Security → Accessibility")
    print("   Add Terminal.app (or your terminal emulator).")
    print()

    listener = HotkeyListener(record_key)
    listener_thread = listener.start()

    show_notification("Voice Input", f"Started. Hotkey: {record_key}")

    try:
        listener_thread.join()
    except KeyboardInterrupt:
        print("\n\nExiting...", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
