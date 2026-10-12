@echo off
rem Record and build the narration voice.
title DomeSim - Local Voice Studio
cd /d "%~dp0.."
py -3.12 local_voice_studio.py %*
if errorlevel 1 pause
