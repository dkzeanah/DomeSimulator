@echo off
rem The website (book gate and dome network): API and client together, for development.
title DomeSim - Web App (dev)
cd /d "%~dp0..\web"
where npm >nul 2>nul || (echo Node.js is not installed: get it from nodejs.org & pause & exit /b 1)
if not exist node_modules call npm install
call npm run dev
pause
