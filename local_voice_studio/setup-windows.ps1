param(
    [switch]$WithLocalAI,
    [string]$CudaTag = "cu126"
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

    # chatterbox-tts hard-pins torch==2.6.0/torchaudio==2.6.0 (see its
    # pyproject.toml), but the plain PyPI index serves a CPU-only build
    # of that exact pin even on a CUDA-capable machine:
    # https://github.com/resemble-ai/chatterbox/issues/95
    # Re-install the SAME pinned versions from PyTorch's own CUDA index
    # so GPU inference actually works -- only when an NVIDIA GPU is
    # present, since there is no point downloading a multi-gigabyte
    # CUDA build for a machine that cannot use one.
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        Write-Host "NVIDIA GPU detected -- installing CUDA-enabled PyTorch ($CudaTag)..."
        & $EnvironmentPython -m pip uninstall -y torch torchaudio
        & $EnvironmentPython -m pip install torch==2.6.0 torchaudio==2.6.0 --index-url "https://download.pytorch.org/whl/$CudaTag"
    } else {
        Write-Host "No NVIDIA GPU detected -- keeping the CPU-only PyTorch build."
    }
}

& $EnvironmentPython -c "import launcher_common as lc; lc.write_config('local_voice_studio', {'action': 'selftest'})"
& $EnvironmentPython -m local_voice_studio
Write-Host ""
Write-Host "Local Voice Studio is ready."
Write-Host "Run: $EnvironmentPython $StudioRoot\local_voice_studio.py"
