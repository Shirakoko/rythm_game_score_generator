@echo off
chcp 65001 >nul
title Music Score Generator Packager
color 0A

echo ===========================================
echo   Music Score Generator Packager
echo ===========================================
echo.

REM Check dependencies
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo [ERROR] pyinstaller not found. Please install:
    echo pip install pyinstaller
    pause
    exit /b 1
)

REM Check main file
if not exist "main.py" (
    echo [ERROR] main.py not found
    pause
    exit /b 1
)

REM Check icon
if not exist "assets\icon.ico" (
    echo [WARNING] Icon not found: assets\icon.ico
    echo Using default icon
    set ICON_OPTION=
) else (
    set ICON_OPTION=--icon=assets\icon.ico
    echo Using icon: assets\icon.ico
)

echo.
echo Cleaning old build files...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del *.spec
if exist "__pycache__" rmdir /s /q __pycache__

echo.
echo Building Music Score Generator...
echo.

REM Main build command
pyinstaller --onefile ^
    --noconsole ^
    %ICON_OPTION% ^
    --name "MusicScoreGenerator" ^
    --clean ^
    --add-data "assets;assets" ^
    --hidden-import=librosa ^
    --hidden-import=customtkinter ^
    --hidden-import=numpy ^
    --hidden-import=scipy ^
    --hidden-import=sklearn ^
    --hidden-import=sklearn.utils._weight_vector ^
    --hidden-import=numba ^
    --hidden-import=llvmlite ^
    --hidden-import=pkg_resources ^
    --collect-all=pydub ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check error messages above.
    pause
    exit /b 1
)

echo.
echo ===========================================
echo   BUILD SUCCESSFUL!
echo   EXE: dist\MusicScoreGenerator.exe
echo   Size: 
for /f %%i in ('dir /b "dist\MusicScoreGenerator.exe"') do (
    for /f "tokens=3" %%j in ('dir "dist\MusicScoreGenerator.exe" ^| findstr "%%i"') do (
        echo          %%j
    )
)
echo ===========================================
echo.

REM Open output folder
echo Open output folder? [Y/N]
choice /c YN /n
if errorlevel 2 goto :end
start "" "dist"

:end
echo.
echo Press any key to exit...
pause >nul