@echo off
echo ========================================
echo   Lancement du Systeme de Resume
echo ========================================
echo.

REM Vérifier si Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas installe ou n'est pas lance.
    echo.
    echo Veuillez installer Docker Desktop depuis:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [OK] Docker est installe
echo.

REM Aller dans le bon dossier
cd /d "%~dp0"

echo Demarrage des services...
echo.
echo ATTENTION: Le premier lancement peut prendre 2-5 minutes
echo (telechargement du modele BART - 1.6 Go)
echo.
echo Appuyez sur Ctrl+C pour arreter les services
echo.

REM Lancer Docker Compose
docker compose up --build

echo.
echo Services arretes.
pause


