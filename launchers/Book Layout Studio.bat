@echo off
rem Lay out, illustrate and edit every book, with the DeepSeek agent (books.studio).
title DomeSim - Book Layout Studio
cd /d "%~dp0.."
py -3.12 -m books.studio %*
if errorlevel 1 pause
