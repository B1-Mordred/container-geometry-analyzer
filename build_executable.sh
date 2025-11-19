#!/bin/bash

# Build script for Container Geometry Analyzer portable executable
# This script creates a standalone executable that can run in air-gapped environments
# Supports Linux, macOS, and Windows (with WSL)

set -e

echo "==============================================="
echo "Container Geometry Analyzer - Build Script"
echo "==============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7+ from https://www.python.org or your package manager"
    echo ""
    echo "On Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "On macOS: brew install python3"
    exit 1
fi

echo "[1/5] Checking Python version..."
python3 --version
echo ""

echo "[2/5] Installing/upgrading PyInstaller..."
pip3 install --upgrade pyinstaller
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install PyInstaller"
    exit 1
fi
echo "PyInstaller installed successfully"
echo ""

echo "[3/5] Installing application dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully"
echo ""

echo "[4/5] Building executable (this may take 2-5 minutes)..."
pyinstaller build_exe.spec --distpath dist --workpath build
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build executable"
    exit 1
fi
echo "Build completed successfully"
echo ""

echo "[5/5] Cleaning up temporary files..."
rm -rf build
echo ""

echo "==============================================="
echo "BUILD COMPLETE!"
echo "==============================================="
echo ""

# Determine executable name based on OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    EXE_NAME="ContainerGeometryAnalyzer"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    EXE_NAME="ContainerGeometryAnalyzer"
else
    EXE_NAME="ContainerGeometryAnalyzer"
fi

echo "Output location:"
echo "  - Executable: dist/ContainerGeometryAnalyzer/$EXE_NAME"
echo ""
echo "USAGE:"
echo "  1. GUI Mode (default):"
echo "     ./dist/ContainerGeometryAnalyzer/$EXE_NAME"
echo ""
echo "  2. CLI Mode with input file:"
echo "     ./dist/ContainerGeometryAnalyzer/$EXE_NAME data.csv"
echo ""
echo "  3. CLI Mode with input and output directory:"
echo "     ./dist/ContainerGeometryAnalyzer/$EXE_NAME data.csv -o output_folder"
echo ""
echo "Note: The executable is self-contained and can run in air-gapped environments"
echo "(no Python installation required on target machine)."
echo ""
