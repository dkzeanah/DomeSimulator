@echo off
rem Review rendered films and leave notes.
title DomeSim - Video Review
cd /d "%~dp0.."
py -3.12 video_review.py %*
if errorlevel 1 pause
