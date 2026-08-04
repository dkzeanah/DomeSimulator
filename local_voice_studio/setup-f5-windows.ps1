param(
    [string]$GradioVersion = "5.49.1"
)

$ErrorActionPreference = "Stop"
$StudioRoot = Split-Path -Parent $PSScriptRoot
$EnvironmentRoot = Join-Path $StudioRoot ".venv-f5"
$RepoRoot = Join-Path $StudioRoot "F5-TTS"
$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue

if (-not $PythonLauncher) {
    throw "Python launcher 'py' was not found. Install 64-bit Python 3.11 from python.org, including Tcl/Tk and the launcher, then run this script again."
}

if (-not (Test-Path $RepoRoot)) {
    $Git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $Git) {
        throw "git was not found. Install Git for Windows, or clone https://github.com/SWivid/F5-TTS manually into $RepoRoot, then run this script again."
    }
    & $Git.Source clone https://github.com/SWivid/F5-TTS.git $RepoRoot
}

# F5-TTS's fine-tune GUI needs its own environment, separate from
# .venv-voice: its own pyproject.toml requires gradio>=6.15.0, but its
# actual finetune_gradio.py script does not start at all on gradio>=6.0
# (a keyword argument gradio 6.x removed from Blocks.launch() -- see
# https://github.com/SWivid/F5-TTS/issues/1239, open/unfixed upstream
# as of this writing). chatterbox-tts, which Local Voice Studio's
# Synthesize tab depends on, hard-pins gradio==6.8.0 exactly. Those two
# constraints cannot both be satisfied in one environment, so this one
# is kept entirely separate and pinned to a gradio version confirmed
# working by that issue's reporters.
& $PythonLauncher.Source -3.11 -m venv $EnvironmentRoot
$EnvironmentPython = Join-Path $EnvironmentRoot "Scripts\python.exe"
& $EnvironmentPython -m pip install --upgrade pip
& $EnvironmentPython -m pip install -e $RepoRoot
& $EnvironmentPython -m pip install "gradio==$GradioVersion"

Write-Host ""
Write-Host "F5-TTS fine-tune environment is ready."
Write-Host "Local Voice Studio's Fine-tune tab picks this up automatically."
Write-Host "To run it directly instead: $EnvironmentRoot\Scripts\f5-tts_finetune-gradio.exe"
