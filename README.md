🇬🇧 **English** | [🇷🇺 Русский](README.ru.md)

[![Latest release](https://img.shields.io/github/v/release/HaiksonLab/ai-voice-input)](https://github.com/HaiksonLab/ai-voice-input/releases) [![Changelog](https://img.shields.io/badge/changelog-view-blue)](CHANGELOG.md)

# 🎙 AI Voice Input

Windows voice-to-text input powered by OpenAI Whisper API.
Press a key — speak — text gets pasted into any active window.

## Features

- Microphone recording triggered by the Menu key (≡)
- Speech recognition via OpenAI Whisper API (excellent quality for any language)
- Result pasted into any active window via clipboard
- **Enter** while recording — stop, transcribe, and send Enter immediately
- **Escape** while recording — cancel without transcription
- **Escape** while transcribing — cancel before text is pasted
- Recording timer in tooltip (shows seconds/minutes elapsed)
- Sound notifications on start, stop, and cancel
- Configurable `prompt` to improve recognition of domain-specific terms
- All settings in `config.ini` — no need to touch the code

## Requirements

- Windows 10 / 11
- [AutoHotkey v2](https://www.autohotkey.com/) (not v1)
- OpenAI API key with Audio API access: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- `curl` (built into Windows 10+)

## Installation

**Option A — Compiled exe (no AutoHotkey required):**
1. Download `ai-voice-input-vX.X.X-exe-win64.zip` from the [latest release](https://github.com/HaiksonLab/ai-voice-input/releases/latest)
2. Extract the archive
3. Rename `config.example.ini` → `config.ini` and set your API key
4. Run `ai_voice_input.exe`

**Option B — Script (requires AutoHotkey v2):**
1. Download or clone the repository
2. Copy `config.example.ini` → `config.ini`
3. Open `config.ini` and set your API key in the `ApiKey=` line
4. Double-click `ai_voice_input.ahk` to run

To auto-start with Windows — create a shortcut to `ai_voice_input.ahk` and place it in the startup folder (`Win+R` → `shell:startup`).

## Configuration

All settings are in `config.ini`:

| Parameter | Description | Default |
|---|---|---|
| `ApiKey` | OpenAI API key | — |
| `Model` | Transcription model | `gpt-4o-transcribe` |
| `Prompt` | Hint for the model (optional) | empty |
| `SoundStart` | Recording start sound (path to WAV) | empty |
| `SoundStop` | Recording stop sound (path to WAV) | empty |
| `SoundCancel` | Cancel sound (path to WAV) | empty |
| `RecordKey` | Hotkey to start/stop recording | `AppsKey` |
| `PasteKey` | Hotkey to re-insert the last transcribed text (empty = disabled) | `RecordKey + V` |
| `MinRecordMs` | Minimum recording duration in ms (shorter = treated as cancel, `0` = disabled) | `1000` |
| `Proxy` | SOCKS5h proxy for OpenAI API requests (optional) | empty |

**RecordKey** uses AutoHotkey key names. Examples:
```ini
RecordKey=AppsKey      ; Menu key (≡) — default
RecordKey=F9           ; F9
RecordKey=^F9          ; Ctrl+F9
RecordKey=!F9          ; Alt+F9
RecordKey=+F9          ; Shift+F9
RecordKey=ScrollLock   ; Scroll Lock
```
Full key list: [autohotkey.com/docs/v2/KeyList.htm](https://www.autohotkey.com/docs/v2/KeyList.htm)

**Proxy** example:
```ini
Proxy=socks5h://127.0.0.1:1080
; With authentication:
; Proxy=socks5h://login:pass@127.0.0.1:1080
```

**Models:** for the current list of supported Whisper models see [platform.openai.com/docs/models](https://platform.openai.com/docs/models).

**Prompt:** optional parameter. Helps the model more accurately recognize professional terms, names, and abbreviations. Add keywords from your domain.

**Sounds:** you can use built-in Windows sounds, for example:
```ini
SoundStart=C:\Windows\Media\Speech On.wav
SoundStop=C:\Windows\Media\Speech Off.wav
SoundCancel=C:\Windows\Media\Speech Misrecognition.wav
```

## Hotkeys

| Key | Action |
|---|---|
| ≡ (Menu key) | Start recording / stop and transcribe |
| Enter *(while recording)* | Stop, transcribe, and press Enter |
| Escape *(while recording)* | Cancel recording |
| Escape *(while transcribing)* | Cancel before text is pasted |

## Known Limitations

### Hallucinations on silence

If nothing was said during recording and you press stop — the API may return arbitrary text instead of an empty string: a fragment from `Prompt` or a thematically similar phrase.

This is **expected behavior** of Whisper and `gpt-4o-transcribe`: models always try to decode something into text and have no "return empty when no speech" mode. Having a `Prompt` amplifies the effect — the model completes text from its context.

**Simple solution:** if you started recording and said nothing — press **Escape** instead of the stop button. Escape cancels recording without calling the API.

## Cost

Whisper API is billed by audio duration.
At time of writing the price is approximately **$0.006 per minute** — about **$1 per 3 hours** of speech.

Current pricing: [platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing)

## License

MIT
