@echo off

echo ======================================================
echo  Creation de l'executable "Navigateur Rapide"...
echo ======================================================
echo.

REM Nettoie les anciens dossiers de build pour eviter les problemes
IF EXIST "dist" ( rmdir /s /q "dist" )
IF EXIST "build" ( rmdir /s /q "build" )
echo Dossiers 'dist' et 'build' nettoyes.
echo.

REM Verifie si le fichier d'icone .ico existe.
IF NOT EXIST "icons\browser.ico" (
    echo [ERREUR] Le fichier icons\browser.ico est introuvable.
    echo.
    echo Veuillez convertir votre fichier browser.svg en browser.ico
    echo et le placer dans le dossier 'icons' avant de continuer.
    echo.
    pause
    exit /b
)

REM Construction en mode dossier (--onedir), plus fiable pour PyQt6. On retire --onefile.
python -m PyInstaller --name "Navigateur Rapide" --noconfirm --windowed --icon="icons\browser.ico" --add-data "accueil.html;." --add-data "icons;icons" navigateur.py

REM Copier les DLLs manquantes (necessaire pour certains systemes)
echo Copie des DLLs supplementaires...
copy "%PYTHONHOME%\vcruntime140_1.dll" "dist\Navigateur Rapide"



echo.
echo ======================================================
echo  Termine !
echo  Votre application se trouve dans le dossier 'dist\Navigateur Rapide'.
echo ======================================================
pause