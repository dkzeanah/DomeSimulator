@echo off
rem Chat with the project's automation agent in a console.
title DomeSim - 02 Project Agent (chat)
cd /d "%~dp0.."
py -3.12 -m project_agent %*
if errorlevel 1 pause
