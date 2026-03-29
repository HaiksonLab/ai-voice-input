#Requires AutoHotkey v2.0
#SingleInstance Force

; ============================================================
;  Голосовой ввод: AppsKey toggle — запись → Whisper API → вставка
; ============================================================

Persistent

; --- Чтение конфига ---
configPath := A_ScriptDir "\config.ini"
apiKey := IniRead(configPath, "Whisper", "ApiKey", "")
model := IniRead(configPath, "Whisper", "Model", "whisper-1")
prompt := IniRead(configPath, "Whisper", "Prompt", "")
soundStart := IniRead(configPath, "Whisper", "SoundStart", "")
soundStop := IniRead(configPath, "Whisper", "SoundStop", "")
soundCancel := IniRead(configPath, "Whisper", "SoundCancel", "")
minRecordMs := Integer(IniRead(configPath, "Whisper", "MinRecordMs", "1500"))
proxy := IniRead(configPath, "Whisper", "Proxy", "")

if (apiKey = "" || apiKey = "sk-YOUR-API-KEY-HERE") {
    MsgBox("Укажите API-ключ OpenAI в файле:`n" configPath, "Voice Input — Ошибка", "Icon!")
    ExitApp
}

; --- Состояние ---
isRecording := false
isTranscribing := false
isCancelled := false
wavFile := A_Temp "\voice_input_recording.wav"
recordStartTime := 0
recordingFmt := ""  ; кеш формата записи

; --- Горячая клавиша: клавиша контекстного меню ---
AppsKey:: {
    global isRecording, wavFile, apiKey, model, prompt, recordStartTime, soundStart, soundStop, minRecordMs, recordingFmt

    if (!isRecording) {
        ; === НАЧАЛО ЗАПИСИ ===
        isRecording := true

        ; Удалить старый файл если есть
        if FileExist(wavFile)
            FileDelete(wavFile)

        ; Открыть устройство записи
        mciSend("close VoiceCapture")
        err1 := mciSendWithError("open new Type waveaudio Alias VoiceCapture")
        if (err1 != "") {
            ToolTip("MCI open error: " err1)
            isRecording := false
            SetTimer(() => ToolTip(), -5000)
            return
        }
        if (recordingFmt = "")
            recordingFmt := DetectRecordingFormat()
        if (recordingFmt != "") {
            mciSend("set VoiceCapture bitspersample " recordingFmt.bits)
            mciSend("set VoiceCapture channels " recordingFmt.ch)
            mciSend("set VoiceCapture samplespersec " recordingFmt.rate)
            mciSend("set VoiceCapture alignment " (recordingFmt.bits // 8 * recordingFmt.ch))
        }
        err2 := mciSendWithError("record VoiceCapture")
        if (err2 != "") {
            ; Формат не сработал — сбросить кеш и попробовать заново
            recordingFmt := ""
            mciSend("close VoiceCapture")
            mciSendWithError("open new Type waveaudio Alias VoiceCapture")
            recordingFmt := DetectRecordingFormat()
            if (recordingFmt != "") {
                mciSend("set VoiceCapture bitspersample " recordingFmt.bits)
                mciSend("set VoiceCapture channels " recordingFmt.ch)
                mciSend("set VoiceCapture samplespersec " recordingFmt.rate)
                mciSend("set VoiceCapture alignment " (recordingFmt.bits // 8 * recordingFmt.ch))
            }
            err2 := mciSendWithError("record VoiceCapture")
            if (err2 != "") {
                ToolTip("MCI record error: " err2)
                mciSend("close VoiceCapture")
                isRecording := false
                SetTimer(() => ToolTip(), -5000)
                return
            }
        }

        PlaySound(soundStart)
        recordStartTime := A_TickCount
        SetTimer(UpdateRecordingTooltip, 1000)
        UpdateRecordingTooltip()
    }
    else {
        StopAndTranscribe(false)
    }
}

; --- Отмена во время распознавания ---
#HotIf isTranscribing
Escape:: {
    global isCancelled, soundCancel
    isCancelled := true
    PlaySound(soundCancel)
    ToolTip("Отмена...")
}
#HotIf

; --- Отмена записи по Escape / остановка с Enter ---
#HotIf isRecording
Escape:: {
    global isRecording, wavFile, soundCancel
    isRecording := false
    SetTimer(UpdateRecordingTooltip, 0)
    mciSend("stop VoiceCapture")
    mciSend("close VoiceCapture")
    try FileDelete(wavFile)
    PlaySound(soundCancel)
    ToolTip("Отмена")
    SetTimer(() => ToolTip(), -800)
}
Enter:: {
    StopAndTranscribe(true)
}
#HotIf

; --- Остановка записи, распознавание и вставка ---
StopAndTranscribe(autoEnter) {
    global isRecording, isTranscribing, isCancelled, wavFile, apiKey, model, prompt, recordStartTime, minRecordMs, soundCancel

    isRecording := false
    SetTimer(UpdateRecordingTooltip, 0)
    ToolTip("⏳ Распознаю... (Esc — отмена)")

    mciSend("stop VoiceCapture")
    mciSend("save VoiceCapture `"" wavFile "`"")
    mciSend("close VoiceCapture")

    if !FileExist(wavFile) {
        ToolTip("Ошибка: WAV файл не создан")
        SetTimer(() => ToolTip(), -3000)
        return
    }
    fileSize := FileGetSize(wavFile)
    if (fileSize < 1000) {
        ToolTip("Ошибка: WAV слишком маленький (" fileSize " байт). Микрофон не пишет.")
        SetTimer(() => ToolTip(), -5000)
        return
    }

    if (minRecordMs > 0 && A_TickCount - recordStartTime < minRecordMs) {
        try FileDelete(wavFile)
        PlaySound(soundCancel)
        ToolTip("Отмена")
        SetTimer(() => ToolTip(), -800)
        return
    }

    isCancelled := false
    PlaySound(soundStop)
    isTranscribing := true
    text := WhisperTranscribe(wavFile, apiKey, model, prompt, proxy)
    isTranscribing := false
    try FileDelete(wavFile)

    if (isCancelled) {
        ToolTip("Отменено")
        SetTimer(() => ToolTip(), -1500)
        return
    }

    if (text = "" || Trim(text) = "") {
        ToolTip("Ничего не распознано")
        SetTimer(() => ToolTip(), -3000)
        return
    }

    prevClip := A_Clipboard
    A_Clipboard := text
    ClipWait(2)
    Send("^v")
    Sleep(100)
    A_Clipboard := prevClip

    if (autoEnter)
        Send("{Enter}")

    ToolTip("✓ " SubStr(text, 1, 60) (StrLen(text) > 60 ? "..." : ""))
    SetTimer(() => ToolTip(), -3000)
}

; --- Обновление тултипа с таймером ---
UpdateRecordingTooltip() {
    global isRecording, recordStartTime
    if (!isRecording) {
        SetTimer(UpdateRecordingTooltip, 0)
        return
    }
    secs := (A_TickCount - recordStartTime) // 1000
    mins := secs // 60
    s := Mod(secs, 60)
    timeStr := mins > 0 ? mins ":" Format("{:02}", s) : secs "с"
    ToolTip("🎙 Запись... " timeStr "  (Menu/Esc)")
}

; --- Воспроизведение звука ---
PlaySound(path) {
    if (path != "" && FileExist(path))
        SoundPlay(path)
}

; --- Whisper API через curl ---
WhisperTranscribe(filePath, key, model, prompt := "", proxy := "") {
    cmd := 'curl -s --max-time 30'
    if (proxy != "")
        cmd .= ' --proxy "' proxy '"'
    cmd .= ' "https://api.openai.com/v1/audio/transcriptions"'
        . ' -H "Authorization: Bearer ' key '"'
        . ' -F "file=@' filePath '"'
        . ' -F "model=' model '"'
        . ' -F "response_format=text"'
    if (prompt != "")
        cmd .= ' -F "prompt=' prompt '"'

    result := RunWaitOutput(cmd)
    result := Trim(result, " `t`r`n")
    return result
}

; --- Запуск команды и получение stdout ---
RunWaitOutput(cmd) {
    tempOut := A_Temp "\voice_input_curl_output.txt"
    try FileDelete(tempOut)

    RunWait(A_ComSpec ' /c ' cmd ' > "' tempOut '" 2>&1',, "Hide")

    if FileExist(tempOut) {
        output := FileRead(tempOut, "UTF-8")
        try FileDelete(tempOut)
        return output
    }
    return ""
}

; --- Обертка mciSendString ---
mciSend(command) {
    buf := Buffer(256, 0)
    DllCall("winmm\mciSendStringW", "Str", command, "Ptr", buf.Ptr, "UInt", 255, "Ptr", 0)
}

; --- mciSendString с возвратом ошибки ---
mciSendWithError(command) {
    buf := Buffer(256, 0)
    errCode := DllCall("winmm\mciSendStringW", "Str", command, "Ptr", buf.Ptr, "UInt", 255, "Ptr", 0, "Int")
    if (errCode != 0) {
        errBuf := Buffer(512, 0)
        DllCall("winmm\mciGetErrorStringW", "UInt", errCode, "Ptr", errBuf.Ptr, "UInt", 255)
        return StrGet(errBuf, "UTF-16")
    }
    return ""
}

; --- Определить поддерживаемый формат записи через waveInOpen WAVE_FORMAT_QUERY ---
DetectRecordingFormat() {
    ; Форматы в порядке предпочтения (Whisper лучше всего с 16kHz 16bit mono)
    formats := [
        {rate: 16000, bits: 16, ch: 1},
        {rate: 22050, bits: 16, ch: 1},
        {rate: 44100, bits: 16, ch: 1},
        {rate: 44100, bits: 16, ch: 2},
        {rate: 8000,  bits: 16, ch: 1},
        {rate: 44100, bits: 8,  ch: 1},
    ]
    for _, fmt in formats {
        wfx := Buffer(18, 0)
        NumPut("UShort", 1,                                      wfx,  0)  ; wFormatTag = PCM
        NumPut("UShort", fmt.ch,                                 wfx,  2)  ; nChannels
        NumPut("UInt",   fmt.rate,                               wfx,  4)  ; nSamplesPerSec
        NumPut("UInt",   fmt.rate * fmt.ch * fmt.bits // 8,      wfx,  8)  ; nAvgBytesPerSec
        NumPut("UShort", fmt.ch * fmt.bits // 8,                 wfx, 12)  ; nBlockAlign
        NumPut("UShort", fmt.bits,                               wfx, 14)  ; wBitsPerSample
        NumPut("UShort", 0,                                      wfx, 16)  ; cbSize
        ; WAVE_MAPPER = 0xFFFFFFFF, WAVE_FORMAT_QUERY = 0x0002
        result := DllCall("winmm\waveInOpen", "Ptr", 0, "UInt", 0xFFFFFFFF, "Ptr", wfx, "Ptr", 0, "Ptr", 0, "UInt", 0x0002, "Int")
        if (result = 0)
            return fmt
    }
    return ""
}
