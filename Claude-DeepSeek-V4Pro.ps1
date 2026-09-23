# ============================================================
# Claude-DeepSeek-V4Pro.ps1
#
# Runs Claude Code through DeepSeek's Anthropic-compatible API.
#
# IMPORTANT:
# These variables apply ONLY to this launcher/process.
# They do not permanently replace normal Claude configuration.
# ============================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $ProjectRoot


# ------------------------------------------------------------
# Retrieve the stored DeepSeek API key.
# ------------------------------------------------------------

$DeepSeekKey = [Environment]::GetEnvironmentVariable(
    "DEEPSEEK_API_KEY",
    "User"
)

if ([string]::IsNullOrWhiteSpace($DeepSeekKey)) {

    Write-Host ""
    Write-Host "DEEPSEEK_API_KEY is not configured." `
        -ForegroundColor Red

    Write-Host ""
    Write-Host "Run Setup-Claude-DeepSeek.ps1 again." `
        -ForegroundColor Yellow

    exit 1
}


# ============================================================
# DEEPSEEK ROUTING
# ============================================================

$env:ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"

$env:ANTHROPIC_AUTH_TOKEN = $DeepSeekKey


# ------------------------------------------------------------
# Claude Code sees an Opus model identifier.
#
# The request is sent to DeepSeek because ANTHROPIC_BASE_URL
# points to DeepSeek rather than Anthropic.
#
# DeepSeek's Anthropic compatibility layer handles the model
# routing to its V4 Pro tier.
# ------------------------------------------------------------

$env:ANTHROPIC_MODEL = "claude-opus-5"

$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "claude-opus-5"

$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "claude-opus-5"


# ------------------------------------------------------------
# Lightweight model for Haiku/subagent work.
# ------------------------------------------------------------

$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "deepseek-flash"

$env:CLAUDE_CODE_SUBAGENT_MODEL = "deepseek-flash"


# ------------------------------------------------------------
# Claude Code behavior recovered from the working session.
# ------------------------------------------------------------

$env:CLAUDE_CODE_EFFORT_LEVEL = "max"

$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = "786432"


# ------------------------------------------------------------
# Prevent an ordinary Anthropic API key from accidentally
# taking precedence in this process.
# ------------------------------------------------------------

Remove-Item Env:ANTHROPIC_API_KEY `
    -ErrorAction SilentlyContinue


# ------------------------------------------------------------
# Status information.
# ------------------------------------------------------------

Write-Host ""
Write-Host "==========================================" `
    -ForegroundColor DarkGray

Write-Host " Claude Code -> DeepSeek V4 Pro" `
    -ForegroundColor Green

Write-Host "==========================================" `
    -ForegroundColor DarkGray

Write-Host "Project :" $ProjectRoot
Write-Host "Endpoint:" $env:ANTHROPIC_BASE_URL
Write-Host "Model   :" $env:ANTHROPIC_MODEL
Write-Host "Effort  :" $env:CLAUDE_CODE_EFFORT_LEVEL

Write-Host ""
Write-Host "Do NOT use /login in this DeepSeek session." `
    -ForegroundColor Yellow

Write-Host ""


# ------------------------------------------------------------
# Forward every command-line argument to Claude.
#
# Examples:
#
# .\Claude-DeepSeek-V4Pro.ps1
#
# .\Claude-DeepSeek-V4Pro.ps1 --continue
#
# .\Claude-DeepSeek-V4Pro.ps1 --resume SESSION-ID
# ------------------------------------------------------------

& claude @args
