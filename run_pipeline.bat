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
  "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"

echo.
echo  Cuando hayas pasado el CAPTCHA de FBref, vuelve aqui y pulsa una tecla.
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

goto :main

:run_step
echo [%~1] Ejecutando %~2 ...
"%PYTHON%" "%DIR%\%~2"
if errorlevel 1 (
  echo Error en "%~2"
  set "FAIL_STEP=%~1 - %~2"
  goto :end
) else (
  echo OK: %~2
)
echo ----------------------------------------
echo.
goto :eof


:main
REM =====================================================
REM                     SCRAPING
REM =====================================================

call :run_step "1/16" "laliga_partidos.py"
call :run_step "2/16" "laliga_estadisticas_partidos.py"
call :run_step "3/16" "estadisticas_jugadores_partidos.py"
call :run_step "4/16" "create_jugadores.py"

REM =====================================================
REM              NORMALIZACION INICIAL
REM =====================================================

REM -- jugadores_raw.csv ya existe tras el paso 4 --
call :run_step "5/16" "generar_jugadores_raw_with_id.py"

call :run_step "6/16" "normalizar_team_stats.py"
call :run_step "7/16" "normalizar_jugadores.py"

REM =====================================================
REM                   GENERACION DE IDs
REM =====================================================

call :run_step "8/16" "generar_ids_para_todos.py"
call :run_step "9/16" "generar_ids_equipos.py"
call :run_step "10/16" "generar_ids_jugadores.py"

REM =====================================================
REM                ARCHIVOS FINALES (MAYUSCULAS)
REM =====================================================

call :run_step "11/16" "Equipo_Estadisticas_Final.py"
call :run_step "12/16" "Jugador_Estadisticas_Final.py"
call :run_step "13/16" "Partidos_Final.py"

REM =====================================================
REM                LIMPIEZA FINAL
REM =====================================================

call :run_step "14/16" "Limpiar_Team_Stats_Final.py"
call :run_step "15/16" "Limpiar_Player_Stats_Final.py"
call :run_step "16/16" "SepararDatosEquipoPartido.py"

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