@echo off
title Pipeline Estadisticas LaLiga
echo ============================================
echo   INICIANDO PIPELINE LALIGA - RUBEN
echo ============================================
echo.

REM ---------- CONFIGURAR RUTAS ----------
set PYTHON="C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos\.venv\Scripts\python.exe"
set DIR="C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos"

echo Usando Python: %PYTHON%
echo Carpeta: %DIR%
echo.

REM ---------- 1) SCRAPEO DE ESTADISTICAS DE EQUIPOS ----------
echo [1/5] Scraping ESTADISTICAS DE EQUIPOS...
%PYTHON% %DIR%\laliga_estadisticas_partidos.py
echo ----------------------------------------
echo.

REM ---------- 2) SCRAPEO DE ESTADISTICAS DE JUGADORES ----------
echo [2/5] Scraping ESTADISTICAS DE JUGADORES...
%PYTHON% %DIR%\estadisticas_jugadores_partidos.py
echo ----------------------------------------
echo.

REM ---------- 3) NORMALIZAR ESTADISTICAS DE EQUIPOS ----------
echo [3/5] Normalizando ESTADISTICAS DE EQUIPOS...
%PYTHON% %DIR%\normalizar_team_stats.py
echo ----------------------------------------
echo.

REM ---------- 4) GENERAR IDs PARA PARTIDOS / EQUIPOS / JUGADORES ----------
echo [4/5] Generando IDs...
%PYTHON% %DIR%\generar_ids_para_todos.py
echo ----------------------------------------
echo.

REM ---------- 5) NORMALIZAR JUGADORES ----------
echo [5/5] Normalizando JUGADORES...
%PYTHON% %DIR%\normalizar_jugadores.py
echo ----------------------------------------
echo.

echo ============================================
echo  PIPELINE COMPLETADO CON ÉXITO
echo ============================================
pause