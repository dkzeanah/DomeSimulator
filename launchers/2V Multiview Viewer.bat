@echo off
rem The 2V dome in several projections at once.
title DomeSim - 2V Multiview Viewer
cd /d "%~dp0.."
py -3.12 "geodesic_2v_multiview (1).py" %*
if errorlevel 1 pause
