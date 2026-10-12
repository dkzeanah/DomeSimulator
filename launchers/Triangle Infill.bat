@echo off
rem Triangle Infill 3-D: fill or cover a wedge dome triangle, every piece numbered,
rem every cut shown on the saw.
title Triangle Infill 3-D
cd /d "%~dp0.."
py -3.12 -m infill.app3d %*
if errorlevel 1 pause
