@echo off
cd /d "%~dp0"
set "BOOK_PYTHON=%LOCALAPPDATA%\Python\pythoncore-3.12-64\python.exe"
if not exist "%BOOK_PYTHON%" set "BOOK_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%BOOK_PYTHON%" (
  echo Python was not found. Run launcher_two_trees_codex.py with your DomeSim Python.
  pause
  exit /b 1
)
"%BOOK_PYTHON%" "%~dp0launcher_two_trees_codex.py"
if errorlevel 1 pause
