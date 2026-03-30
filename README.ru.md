[🇬🇧 English](README.md) | 🇷🇺 **Русский**

[![Последний релиз](https://img.shields.io/github/v/release/HaiksonLab/ai-voice-input)](https://github.com/HaiksonLab/ai-voice-input/releases) [![Список изменений](https://img.shields.io/badge/changelog-view-blue)](CHANGELOG.md)

# 🎙 AI Voice Input

Голосовой ввод текста для Windows на базе OpenAI Whisper API.
Нажмите клавишу — скажите — текст вставится в любое активное окно.

## Возможности

- Запись с микрофона по нажатию клавиши контекстного меню (≡)
- Распознавание речи через OpenAI Whisper API (отличное качество русского языка)
- Вставка результата в любое активное окно через буфер обмена
- **Enter** во время записи — остановить, распознать и сразу отправить
- **Escape** во время записи — отменить без распознавания
- **Escape** во время распознавания — отменить до вставки текста
- Таймер записи в тултипе (показывает сколько секунд/минут идёт запись)
- Звуковые сигналы на старт, стоп и отмену
- Настраиваемый `prompt` для улучшения качества распознавания терминов
- Все параметры вынесены в `config.ini` — не нужно трогать код

## Требования

- Windows 10 / 11
- [AutoHotkey v2](https://www.autohotkey.com/) (не v1)
- API-ключ OpenAI с доступом к Audio API: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- `curl` (встроен в Windows 10+)

## Установка

**Вариант А — скомпилированный exe (AutoHotkey не нужен):**
1. Скачайте `ai-voice-input-vX.X.X-exe-win64.zip` из [последнего релиза](https://github.com/HaiksonLab/ai-voice-input/releases/latest)
2. Распакуйте архив
3. Переименуйте `config.example.ini` → `config.ini` и укажите API-ключ
4. Запустите `ai_voice_input.exe`

**Вариант Б — скрипт (требуется AutoHotkey v2):**
1. Скачайте или клонируйте репозиторий
2. Скопируйте `config.example.ini` → `config.ini`
3. Откройте `config.ini` и укажите свой API-ключ в строке `ApiKey=`
4. Запустите `ai_voice_input.ahk` двойным кликом

Для автозапуска вместе с Windows — создайте ярлык на `ai_voice_input.ahk` и поместите его в папку автозагрузки (`Win+R` → `shell:startup`).

## Настройка

Все параметры находятся в файле `config.ini`:

| Параметр | Описание | По умолчанию |
|---|---|---|
| `ApiKey` | API-ключ OpenAI | — |
| `Model` | Модель транскрипции | `gpt-4o-transcribe` |
| `Prompt` | Подсказка для модели (опционально) | пусто |
| `SoundStart` | Звук начала записи (путь к WAV) | пусто |
| `SoundStop` | Звук остановки записи (путь к WAV) | пусто |
| `SoundCancel` | Звук отмены (путь к WAV) | пусто |
| `RecordKey` | Клавиша старта/стопа записи | `AppsKey` |
| `MinRecordMs` | Минимальная длительность записи в мс (короче — считается отменой, `0` = отключено) | `1000` |
| `Proxy` | SOCKS5h прокси для запросов к OpenAI API (опционально) | пусто |

**RecordKey** использует имена клавиш AutoHotkey. Примеры:
```ini
RecordKey=AppsKey      ; клавиша меню (≡) — по умолчанию
RecordKey=F9           ; F9
RecordKey=^F9          ; Ctrl+F9
RecordKey=!F9          ; Alt+F9
RecordKey=+F9          ; Shift+F9
RecordKey=ScrollLock   ; Scroll Lock
```
Полный список клавиш: [autohotkey.com/docs/v2/KeyList.htm](https://www.autohotkey.com/docs/v2/KeyList.htm)

**Прокси** пример:
```ini
Proxy=socks5h://127.0.0.1:1080
; С аутентификацией:
; Proxy=socks5h://login:pass@127.0.0.1:1080
```

**Про модели:** актуальный список поддерживаемых моделей Whisper смотрите на [platform.openai.com/docs/models](https://platform.openai.com/docs/models).

**Про `Prompt`:** необязательный параметр. Помогает модели точнее распознавать профессиональные термины, имена, аббревиатуры. Укажите в нём ключевые слова из вашей области.

**Про звуки:** можно использовать встроенные звуки Windows, например:
```ini
SoundStart=C:\Windows\Media\Speech On.wav
SoundStop=C:\Windows\Media\Speech Off.wav
SoundCancel=C:\Windows\Media\Speech Misrecognition.wav
```

## Горячие клавиши

| Клавиша | Действие |
|---|---|
| ≡ (Menu key) | Начать запись / остановить и распознать |
| Enter *(во время записи)* | Остановить, распознать и нажать Enter |
| Escape *(во время записи)* | Отменить запись |
| Escape *(во время распознавания)* | Отменить до вставки текста |

## Известные ограничения

### Галлюцинации при тишине

Если во время записи ничего не было сказано, а затем нажать кнопку остановки — API может вернуть не пустую строку, а произвольный текст: фрагмент из `Prompt` или тематически похожую фразу.

Это **ожидаемое поведение** Whisper и `gpt-4o-transcribe`: модели всегда пытаются декодировать что-то в текст и не имеют режима "вернуть пусто при отсутствии речи". Наличие `Prompt` усиливает эффект — модель достраивает текст из его контекста.

**Решение простое:** если вы начали запись и не сказали ничего — нажмите **Escape** вместо кнопки остановки. Escape отменяет запись без обращения к API.

## Стоимость

Whisper API тарифицируется по времени аудио.
На момент публикации цена составляет около **$0.006 за минуту** — это примерно **$1 за 3 часа** разговора.

Актуальные цены: [platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing)

## Лицензия

MIT
