# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.1] - 2026-03-29

### Added
- `RecordKey` config option — customize the start/stop hotkey (default: `AppsKey`)
- `Proxy` config option — SOCKS5h proxy support for OpenAI API requests

### Fixed
- MCI recording compatibility on audio drivers that require explicit `alignment` parameter
- Automatic detection of the best supported recording format via `waveInOpen WAVE_FORMAT_QUERY` with fallback

## [1.0.0] - 2026-03-25

### Added
- Initial release
- Voice recording via Menu key (≡)
- Speech recognition via OpenAI Whisper API
- Text insertion into any active window via clipboard
- `Enter` to stop and transcribe, `Escape` to cancel
- Recording timer in tooltip
- Sound notifications (start, stop, cancel)
- Configurable `prompt`, `model`, sounds, and `MinRecordMs` via `config.ini`
