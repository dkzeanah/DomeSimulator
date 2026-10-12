@echo off
rem The desk where the wedge book is built.
title DomeSim - Book Studio
cd /d "%~dp0.."
py -3.12 book_studio.py %*
if errorlevel 1 pause
