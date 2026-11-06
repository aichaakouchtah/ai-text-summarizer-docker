@echo off
echo ========================================
echo   Arret du Systeme de Resume
echo ========================================
echo.

REM Vérifier si Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas installe ou n'est pas lance.
    pause
    exit /b 1
)

REM Aller dans le bon dossier
cd /d "%~dp0"

echo Arret des services...
docker compose down

echo.
echo Services arretes avec succes.
echo.
pause


