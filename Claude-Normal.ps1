# ============================================================
# Claude-Normal.ps1
#
# Starts normal Claude Code using Anthropic.
#
# DeepSeek routing variables are removed ONLY from this
# process. Nothing is deleted from your Claude configuration,
# projects, sessions, history, or permissions.
# ============================================================

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $ProjectRoot


# ------------------------------------------------------------
# Remove DeepSeek/alternate-provider overrides from this
# process.
# ------------------------------------------------------------

$Variables = @(
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL",
    "CLAUDE_CODE_EFFORT_LEVEL",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
)

foreach ($Name in $Variables) {
    Remove-Item "Env:$Name" -ErrorAction SilentlyContinue
}


Write-Host ""
Write-Host "==========================================" `
    -ForegroundColor DarkGray

Write-Host " Normal Anthropic Claude Code" `
    -ForegroundColor Cyan

Write-Host "==========================================" `
    -ForegroundColor DarkGray

Write-Host "Project:" $ProjectRoot
Write-Host ""
Write-Host "Normal /login and /model behavior enabled."
Write-Host ""


# Forward arguments to Claude.

& claude @args
