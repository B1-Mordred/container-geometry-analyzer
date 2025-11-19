@echo off
REM Build script for Container Geometry Analyzer portable .exe
REM This script creates a standalone executable that can run in air-gapped environments

echo ===============================================
echo Container Geometry Analyzer - Build Script
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version
echo.

echo [2/5] Installing/upgrading PyInstaller...
pip install --upgrade pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo PyInstaller installed successfully
echo.

echo [3/5] Installing application dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

echo [4/5] Building executable (this may take 2-5 minutes)...
pyinstaller build_exe.spec --distpath dist --workpath build
if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)
echo Build completed successfully
echo.

echo [5/5] Cleaning up temporary files...
rmdir /s /q build
echo.

echo ===============================================
echo BUILD COMPLETE!
echo ===============================================
echo.
echo Output location:
echo   - Single executable: dist\ContainerGeometryAnalyzer.exe
echo   - With dependencies: dist\ContainerGeometryAnalyzer\ContainerGeometryAnalyzer.exe
echo.
echo USAGE:
echo   1. GUI Mode (default):
echo      ContainerGeometryAnalyzer.exe
echo.
echo   2. CLI Mode with input file:
echo      ContainerGeometryAnalyzer.exe data.csv
echo.
echo   3. CLI Mode with input and output directory:
echo      ContainerGeometryAnalyzer.exe data.csv -o output_folder
echo.
echo Note: The executable is self-contained and can run in air-gapped environments
echo (no Python installation required on target machine).
echo.
pause
