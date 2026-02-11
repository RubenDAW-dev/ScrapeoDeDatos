@echo off
title Pipeline Estadisticas LaLiga - Ruben
echo ============================================
echo     INICIANDO PIPELINE COMPLETO LALIGA
echo ============================================
echo.

set "PYTHON=C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos\.venv\Scripts\python.exe"
set "DIR=C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos"

echo Usando Python: %PYTHON%
echo Carpeta: %DIR%
echo.

REM =====================================================
REM                 SCRAPING PRINCIPAL
REM =====================================================

echo [1/13] Scraping ESTADISTICAS EQUIPOS (match reports)...
%PYTHON% "%DIR%\laliga_estadisticas_partidos.py"
echo.

echo [2/13] Scraping ESTADISTICAS JUGADORES (match reports)...
%PYTHON% "%DIR%\estadisticas_jugadores_partidos.py"
echo.

echo [3/13] Scraping listado JUGADORES LALIGA (FBref)...
%PYTHON% "%DIR%\create_jugadores.py"
echo.

REM =====================================================
REM              NORMALIZACIONES BASE
REM =====================================================

echo [4/13] Normalizando ESTADISTICAS EQUIPOS iniciales...
%PYTHON% "%DIR%\normalizar_team_stats.py"
echo.

echo [5/13] Normalizando ESTADISTICAS JUGADORES iniciales...
%PYTHON% "%DIR%\normalizar_jugadores.py"
echo.

REM =====================================================
REM                  GENERACIÓN DE IDs
REM =====================================================

echo [6/13] Generando MATCH_ID (partidos, equipos, jugadores)...
%PYTHON% "%DIR%\generar_ids_para_todos.py"
echo.

echo [7/13] Generando TEAM_ID...
%PYTHON% "%DIR%\generar_ids_equipos.py"
echo.

echo [8/13] Generando PLAYER_ID...
%PYTHON% "%DIR%\generar_ids_jugadores.py"
echo.

REM =====================================================
REM                FICHEROS FINALES (MAYÚSCULA)
REM =====================================================

echo [9/13] Generando TEAM_STATS_FINAL.CSV...
%PYTHON% "%DIR%\Equipo_Estadisticas_Final.py"
echo.

echo [10/13] Generando PLAYER_STATS_FINAL.CSV...
%PYTHON% "%DIR%\Jugador_Estadisticas_Final.py"
echo.

echo [11/13] Generando PARTIDOS_FINAL.CSV...
%PYTHON% "%DIR%\Partidos_Final.py"
echo.

echo ============================================
echo      PIPELINE COMPLETADO CON ÉXITO
echo ============================================
pause