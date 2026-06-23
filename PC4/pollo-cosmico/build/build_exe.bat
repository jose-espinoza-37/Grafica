@echo off
REM build_exe.bat
REM ---------------
REM Genera el ejecutable .exe del juego. Ejecutar desde la carpeta build/
REM con el entorno virtual activado y las dependencias instaladas
REM (pip install -r ../requirements.txt).

pyinstaller --noconfirm --onefile --windowed ^
    --name "ElPolloCosmico" ^
    --icon "icon.ico" ^
    --add-data "../assets;assets" ^
    "../main.py"

echo.
echo Listo. El ejecutable esta en build\dist\ElPolloCosmico.exe
echo Sube esa carpeta (o un .zip de ella) a itch.io como build para Windows.
pause
