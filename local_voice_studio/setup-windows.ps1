param(
    [switch]$WithLocalAI
)

$ErrorActionPreference = "Stop"
$StudioRoot = Split-Path -Parent $PSScriptRoot
$EnvironmentRoot = Join-Path $StudioRoot ".venv-voice"
$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue

if (-not $PythonLauncher) {
    throw "Python launcher 'py' was not found. Install 64-bit Python 3.11 from python.org, including Tcl/Tk and the launcher, then run this script again."
}

& $PythonLauncher.Source -3.11 -m venv $EnvironmentRoot
$EnvironmentPython = Join-Path $EnvironmentRoot "Scripts\python.exe"
& $EnvironmentPython -m pip install --upgrade pip
& $EnvironmentPython -m pip install -r (Join-Path $PSScriptRoot "requirements-core.txt")

if ($WithLocalAI) {
    & $EnvironmentPython -m pip install -r (Join-Path $PSScriptRoot "requirements-local-ai.txt")
}

& $EnvironmentPython -c "import launcher_common as lc; lc.write_config('local_voice_studio', {'action': 'selftest'})"
& $EnvironmentPython -m local_voice_studio
Write-Host ""
Write-Host "Local Voice Studio is ready."
Write-Host "Run: $EnvironmentPython $StudioRoot\local_voice_studio.py"
