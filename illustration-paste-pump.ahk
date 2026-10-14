; =====================================================================
; illustration-paste-pump.ahk  (AutoHotkey v2)
; ---------------------------------------------------------------------
; Loads every fenced ```text prompt from a prompts markdown file and
; pastes them one by one into whatever window is focused — back to back —
; so you can feed a whole campaign's worth of image prompts into
; ChatGPT / Gemini without copy-pasting by hand.
;
;   F9   start / pause the pump
;   F10  skip the current prompt (advance to the next one)
;   F7   shorten the pause between prompts (min 2 s)
;   F8   lengthen the pause between prompts (max 60 s)
;   F6   toggle auto-send (press Enter after each paste)
;   F5   reload the prompts file
;   Esc  stop the pump and restore your old clipboard
;
; =====================================================================
#Requires AutoHotkey v2.0
#SingleInstance Force

; ---------------------------------------------------------------------
; Settings
; ---------------------------------------------------------------------
global PromptsFile := A_ScriptDir . "\book\campaign-illustration-prompts.md"
    ; The prompts file. Fenced ```text blocks are the prompts; everything
    ; else (headings, tables, rules) is ignored. Point this at
    ; book\illustration-prompts.md to pump the book series instead.
    ; For the whole launch at once, join several files with "|":
    ;   PromptsFile := A_ScriptDir . "\book\campaign-illustration-prompts.md|"
    ;       . A_ScriptDir . "\deliverables\campaign\asset-prompts.md|"
    ;       . A_ScriptDir . "\book\illustration-prompts.md"
    ; The pump fires every prompt in every file, back to back, in order.
global DelayMs := 8000
    ; Pause after a paste before the next one fires. Long enough for the
    ; image generator to start working; adjust live with F7 / F8.
global AutoSend := false
    ; true = press Enter shortly after each paste (fires the prompt).
    ; false = you press Send yourself. Toggle with F6.

; ---------------------------------------------------------------------
; State
; ---------------------------------------------------------------------
global Prompts := []
global Index := 1
global Running := false
global OriginalClip := ""
global PendingTimer := false

; ---------------------------------------------------------------------
; Loading
; ---------------------------------------------------------------------
LoadPrompts() {
    global Prompts
    files := StrSplit(PromptsFile, "|")
    missing := ""
    for file in files {
        if !FileExist(Trim(file))
            missing .= (missing ? "`n" : "") . Trim(file)
    }
    if (missing != "") {
        ToolTip("Prompts file not found:`n" . missing)
        SetTimer(() => ToolTip(), -6000)
        return
    }
    Prompts := []
    for file in files {
        text := FileRead(Trim(file), "UTF-8")
        pos := 1
        while (pos := RegExMatch(text, "s)``````text\R\K(.*?)(?=``````)", &m, pos)) {
            prompt := Trim(m[0], " `t`r`n")
            if prompt
                Prompts.Push(prompt)
            pos := m.Pos + m.Len
        }
    }
    ToolTip("Loaded " . Prompts.Length . " prompts from "
        . files.Length . " file" . (files.Length = 1 ? "" : "s")
        . "`nF9 to start.")
    SetTimer(() => ToolTip(), -4000)
}

; ---------------------------------------------------------------------
; The pump
; ---------------------------------------------------------------------
PasteNow() {
    global Prompts, Index, Running, OriginalClip, PendingTimer
    if (Index > Prompts.Length) {
        FinishPump("All " . Prompts.Length . " prompts fired. Done.")
        return
    }
    prompt := Prompts[Index]
    A_Clipboard := prompt
    Sleep 300                     ; let the clipboard settle
    Send("^v")
    if AutoSend {
        SetTimer(() => Send("{Enter}"), -1200)
    }
    preview := SubStr(RegExReplace(prompt, "\s+", " "), 1, 58)
    ToolTip("Fired " . Index . " / " . Prompts.Length . "`n"
        . preview . (StrLen(prompt) > 58 ? "…" : "") . "`n"
        . "next in " . Round(DelayMs / 1000, 1) . " s"
        . (AutoSend ? " · auto-send ON" : "") . "`n"
        . "F9 pause · F10 skip · F7/F8 pace · Esc stop")
    SetTimer(PasteNext, -DelayMs)
}

PasteNext() {
    global Index
    Index += 1
    PasteNow()
}

FinishPump(message) {
    global Running, OriginalClip
    Running := false
    if (OriginalClip != "")
        A_Clipboard := OriginalClip
    OriginalClip := ""
    ToolTip(message)
    SetTimer(() => ToolTip(), -6000)
}

; ---------------------------------------------------------------------
; Hotkeys
; ---------------------------------------------------------------------
F9:: {
    global Running, Index, OriginalClip
    if (Running) {
        Running := false
        SetTimer(PasteNext, 0)
        if (OriginalClip != "")
            A_Clipboard := OriginalClip
        OriginalClip := ""
        ToolTip("Paused at prompt " . Index . " of " . Prompts.Length
            . "`nF9 resumes.")
    } else {
        if (Prompts.Length == 0)
            LoadPrompts()
        OriginalClip := ClipboardAll()
        Running := true
        PasteNow()
    }
}

F10:: {
    global Running, Index
    if (!Running)
        return
    Index += 1
    PasteNow()
}

F7:: {
    global DelayMs
    DelayMs := Max(2000, DelayMs - 1000)
    ToolTip("Pace: " . Round(DelayMs / 1000, 1) . " s between prompts")
    SetTimer(() => ToolTip(), -1500)
}

F8:: {
    global DelayMs
    DelayMs := Min(60000, DelayMs + 1000)
    ToolTip("Pace: " . Round(DelayMs / 1000, 1) . " s between prompts")
    SetTimer(() => ToolTip(), -1500)
}

F6:: {
    global AutoSend
    AutoSend := !AutoSend
    ToolTip("Auto-send " . (AutoSend ? "ON — Enter fires after each paste"
        : "OFF — you press Send yourself"))
    SetTimer(() => ToolTip(), -2000)
}

F5::LoadPrompts()

Esc:: {
    global Running
    if (Running) {
        FinishPump("Stopped at prompt " . Index . " of " . Prompts.Length . ".")
    }
}

; ---------------------------------------------------------------------
; Start
; ---------------------------------------------------------------------
LoadPrompts()
ToolTip("illustration-paste-pump ready`nF9 start · F5 reload · Esc stop")
SetTimer(() => ToolTip(), -5000)
