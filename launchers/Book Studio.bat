@echo off
rem Lay out, illustrate and edit the books, with the DeepSeek agent.
title DomeSim - Book Studio
cd /d "%~dp0.."
py -3.12 -m books.studio %*
if errorlevel 1 pause
