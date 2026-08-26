@echo off
echo =======================================================
echo     Actualizador de Antigravity IDE
echo =======================================================
echo.
echo Por favor, cierra la ventana de Antigravity IDE ahora.
echo Esperando a que el programa se cierre por completo...
echo.

:wait_loop
tasklist | find /i "antigravity-ide" > nul
if %ERRORLEVEL% equ 0 (
    timeout /t 3 /nobreak > nul
    goto wait_loop
)

echo Antigravity IDE se ha cerrado.
echo Iniciando la actualizacion a la ultima version...
echo.
winget upgrade --id Google.AntigravityIDE --silent --accept-package-agreements --accept-source-agreements

echo.
echo =======================================================
echo Actualizacion completada exitosamente.
echo Ya puedes volver a abrir Antigravity IDE.
echo =======================================================
pause
