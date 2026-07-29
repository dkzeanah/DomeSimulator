#!/usr/bin/env sh
set -eu

studio_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
environment_root="$studio_root/.venv-voice"
python3.11 -m venv "$environment_root"
"$environment_root/bin/python" -m pip install --upgrade pip
"$environment_root/bin/python" -m pip install \
  -r "$studio_root/local_voice_studio/requirements-core.txt"

if [ "${1:-}" = "--with-local-ai" ]; then
  "$environment_root/bin/python" -m pip install \
    -r "$studio_root/local_voice_studio/requirements-local-ai.txt"
fi

"$environment_root/bin/python" -m local_voice_studio --selftest
printf '%s\n' "Run: $environment_root/bin/python $studio_root/local_voice_studio.py"
