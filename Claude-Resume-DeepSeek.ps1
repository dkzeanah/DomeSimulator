# ============================================================
# Claude-Resume-DeepSeek.ps1
#
# Displays Claude's resume picker while routed through
# DeepSeek V4 Pro.
# ============================================================

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$DeepSeekLauncher = Join-Path `
    $ProjectRoot `
    "Claude-DeepSeek-V4Pro.ps1"

& $DeepSeekLauncher --resume
