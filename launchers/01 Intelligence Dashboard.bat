@echo off
rem What the observer learned, playbooks, DeepSeek and the agent, in your browser.
title DomeSim - 01 Intelligence Dashboard
cd /d "%~dp0.."
py -3.12 -m intelligence.dashboard %*
if errorlevel 1 pause
