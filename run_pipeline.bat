@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Pipeline Estadisticas LaLiga - Ruben

REM =====================================================
REM          ABRIR CHROME PARA PASAR CAPTCHA
REM =====================================================

echo Abriendo Chrome para pasar CAPTCHA...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="C:\ChromeScraping" ^
  https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"

echo.
echo  Cuando hayas pasado el CAPTCHA de FBref, vuelve aquí y pulsa una tecla.
pause >nul
echo CAPTCHA pasado. Continuando pipeline...
echo ----------------------------------------
echo.


echo ============================================
echo      INICIANDO PIPELINE COMPLETO LALIGA
echo ============================================
echo.

REM ---------- CONFIGURAR RUTAS ----------
set "PYTHON=C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos\.venv\Scripts\python.exe"
set "DIR=C:\Users\RubenVillarGonzalez\Desktop\TFG\Escrapeo de datos"

echo Usando Python: %PYTHON%
echo Carpeta: %DIR%
echo.

set "FAIL_STEP="

REM *** IMPORTANTE: SALTO AL MAIN PARA NO EJECUTAR LA FUNCION ***
goto :main

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


:main
REM =====================================================
REM                     SCRAPING
REM =====================================================

call :run_step "1/13" "laliga_estadisticas_partidos.py"
call :run_step "2/13" "estadisticas_jugadores_partidos.py"
call :run_step "3/13" "create_jugadores.py"

REM =====================================================
REM              NORMALIZACION INICIAL
REM =====================================================

call :run_step "4/13" "normalizar_team_stats.py"
call :run_step "5/13" "normalizar_jugadores.py"

REM =====================================================
REM                   GENERACIÓN DE IDs
REM =====================================================

call :run_step "6/13" "generar_ids_para_todos.py"
call :run_step "7/13" "generar_ids_equipos.py"
call :run_step "8/13" "generar_ids_jugadores.py"

REM =====================================================
REM                ARCHIVOS FINALES (MAYÚSCULAS)
REM =====================================================

call :run_step "9/13"  "Equipo_Estadisticas_Final.py"
call :run_step "10/13" "Jugador_Estadisticas_Final.py"
call :run_step "11/13" "Partidos_Final.py"

REM =====================================================
REM                LIMPIEZA FINAL
REM =====================================================

call :run_step "12/13" "Limpiar_Team_Stats_Final.py"
call :run_step "13/13" "Limpiar_Player_Stats_Final.py"


:end
echo ============================================
if defined FAIL_STEP (
  echo    PIPELINE FINALIZADO CON ERRORES EN: %FAIL_STEP%
) else (
  echo    PIPELINE COMPLETADO CON EXITO
)
echo ============================================
echo.
pause
endlocal