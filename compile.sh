#!/bin/bash

# Compiles the project to linux binary

MAIN_DIR="/home/p1geon/Documents/code/music-share" # change this path
MAIN_FILE="$MAIN_DIR/main.py"
ASSETS_DIR="$MAIN_DIR/assets"
SCRIPTS_DIR="$MAIN_DIR/scripts"

# PyInstaller command
pyinstaller --onefile --windowed \
    --add-data "$ASSETS_DIR:assets" \
    --add-data "$SCRIPTS_DIR:scripts" \
    $MAIN_FILE
