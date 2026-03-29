# 🎙 AI Voice Input — macOS

macOS-версия голосового ввода через OpenAI Whisper API.
Нажми горячую клавишу — говори — текст вставляется в любое активное окно.

Полный порт оригинального Windows-скрипта на Python.

## Возможности

- Запись с микрофона по горячей клавише (по умолчанию F9)
- Распознавание речи через OpenAI Whisper API (отличное качество для любого языка)
- Результат вставляется в активное окно через буфер обмена (Cmd+V)
- **Enter** во время записи — остановить, распознать и нажать Enter
- **Escape** во время записи — отменить без распознавания
- **Escape** во время распознавания — отменить до вставки текста
- Таймер записи в терминале (секунды/минуты)
- Звуковые уведомления при старте, стопе и отмене
- Настраиваемый `Prompt` для улучшения распознавания терминов
- Все настройки в `config.ini` — код менять не нужно

## Требования

- macOS 12+ (Monterey или новее)
- Python 3.9+
- OpenAI API ключ с доступом к Audio API: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- PortAudio (устанавливается через Homebrew)

## Установка

### 1. Установить PortAudio (необходим для записи звука)

```bash
brew install portaudio
```

### 2. Установить Python-зависимости

```bash
pip3 install -r requirements.txt
```

### 3. Настроить конфиг

```bash
cp config.example.mac.ini config.ini
```

Откройте `config.ini` и укажите ваш API ключ в строке `ApiKey=`.

### 4. Выдать разрешения

macOS требует разрешение **Accessibility** для перехвата клавиш и вставки текста:

1. **System Preferences** → **Privacy & Security** → **Accessibility**
2. Добавьте ваш терминал (Terminal.app, iTerm2, Warp и т.д.)

Также потребуется разрешение на **микрофон** при первом запуске.

### 5. Запустить

```bash
python3 ai_voice_input_mac.py
```

Для работы в фоне:

```bash
nohup python3 ai_voice_input_mac.py &
```

### Автозапуск при входе в систему

Создайте `.plist` файл для launchd:

```bash
cat > ~/Library/LaunchAgents/com.aivoiceinput.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aivoiceinput</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/ai_voice_input_mac.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF
```

Замените `/path/to/` на реальный путь. Затем:

```bash
launchctl load ~/Library/LaunchAgents/com.aivoiceinput.plist
```

## Настройка

Все настройки в `config.ini`:

| Параметр | Описание | По умолчанию |
|---|---|---|
| `ApiKey` | API ключ OpenAI | — |
| `Model` | Модель транскрипции | `gpt-4o-transcribe` |
| `Prompt` | Подсказка для модели (опционально) | пусто |
| `SoundStart` | Звук начала записи (путь к файлу) | системный звук |
| `SoundStop` | Звук окончания записи (путь к файлу) | системный звук |
| `SoundCancel` | Звук отмены (путь к файлу) | системный звук |
| `RecordKey` | Горячая клавиша старт/стоп | `f9` |
| `MinRecordMs` | Минимальная длительность записи в мс | `1000` |
| `Proxy` | SOCKS5h прокси (опционально) | пусто |

### Формат RecordKey

```ini
RecordKey=f9           ; F9 (по умолчанию)
RecordKey=f5           ; F5
RecordKey=ctrl+f9      ; Ctrl+F9
RecordKey=cmd+shift+f9 ; Cmd+Shift+F9
RecordKey=alt+f9       ; Option+F9
```

### Доступные звуки macOS

```ini
SoundStart=/System/Library/Sounds/Tink.aiff
SoundStop=/System/Library/Sounds/Pop.aiff
SoundCancel=/System/Library/Sounds/Basso.aiff
```

Другие встроенные звуки: `Blow`, `Bottle`, `Frog`, `Funk`, `Glass`, `Hero`, `Morse`, `Ping`, `Purr`, `Sosumi`, `Submarine`, `Tink`, `Pop`, `Basso`.

### Прокси

```ini
Proxy=socks5h://127.0.0.1:1080
; С авторизацией:
; Proxy=socks5h://login:pass@127.0.0.1:1080
```

## Горячие клавиши

| Клавиша | Действие |
|---|---|
| F9 (или настроенная) | Начать/остановить запись |
| Enter *(во время записи)* | Остановить, распознать и нажать Enter |
| Escape *(во время записи)* | Отменить запись |
| Escape *(во время распознавания)* | Отменить до вставки текста |
| Ctrl+C *(в терминале)* | Выход |

## Известные ограничения

### Галлюцинации на тишине

Если ничего не сказано во время записи — API может вернуть произвольный текст. Это ожидаемое поведение Whisper. **Решение:** нажмите **Escape** вместо горячей клавиши стоп.

### Accessibility-разрешения

При первом запуске macOS может заблокировать перехват клавиш. Добавьте терминал в настройках Accessibility.

### Отличия от Windows-версии

| Функция | Windows (AHK) | macOS (Python) |
|---|---|---|
| Тултипы | Нативные Windows ToolTip | Терминальный вывод + Notification Center |
| Звуки | Любой WAV | Любой формат (через afplay) |
| Горячая клавиша | AppsKey по умолчанию | F9 по умолчанию (Menu key нет на Mac) |
| Вставка | Ctrl+V | Cmd+V (через AppleScript) |
| Автозапуск | shell:startup | launchd plist |

## Стоимость

Whisper API тарифицируется по длительности аудио.
Примерно **$0.006 за минуту** — около **$1 за 3 часа** речи.

Актуальные цены: [platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing)

## Лицензия

MIT
