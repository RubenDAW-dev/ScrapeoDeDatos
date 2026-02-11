@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Pipeline Estadisticas LaLiga

echo ============================================
echo   INICIANDO PIPELINE LALIGA - RUBEN
echo ============================================
echo.

REM ---------- CONFIGURAR RUTAS ----------
set "PYTHON=C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos\.venv\Scripts\python.exe"
set "DIR=C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos"

echo Usando Python: %PYTHON%
echo Carpeta: %DIR%
echo.

REM Función para chequear errorlevel
set "FAIL_STEP="

:run_step
REM %1 = etiqueta visible, %2 = script
echo [%~1] Ejecutando %~2 ...
"%PYTHON%" "%DIR%\%~2"
if errorlevel 1 (
  echo ❌ Error en "%~2"
  set "FAIL_STEP=%~1 - %~2"
  goto :end
) else (
  echo ✔ OK: %~2
)
echo ----------------------------------------
echo.
goto :eof

REM ---------- 1) SCRAPEO ESTADISTICAS DE EQUIPOS (por partido) ----------
call :run_step "1/7" "laliga_estadisticas_partidos.py"

REM ---------- 2) SCRAPEO ESTADISTICAS DE JUGADORES (por partido) ----------
call :run_step "2/7" "estadisticas_jugadores_partidos.py"

REM ---------- 3) LISTADO DE EQUIPOS (FBref) ----------
call :run_step "3/7" "create_equipos_fbref.py"

REM ---------- 4) LISTADO DE JUGADORES (FBref) ----------
call :run_step "4/7" "create_jugadores.py"

REM ---------- 5) NORMALIZAR ESTADISTICAS DE EQUIPOS ----------
call :run_step "5/7" "normalizar_team_stats.py"

REM ---------- 6) GENERAR IDs PARA PARTIDOS / EQUIPOS / JUGADORES ----------
call :run_step "6/7" "generar_ids_para_todos.py"

REM ---------- 7) NORMALIZAR JUGADORES ----------
call :run_step "7/7" "normalizar_jugadores.py"

:end
echo ============================================
if defined FAIL_STEP (
  echo  PIPELINE FINALIZADO CON ERRORES en: %FAIL_STEP%
) else (
  echo  PIPELINE COMPLETADO CON EXITO
)
echo ============================================
echo.
pause
endlocal