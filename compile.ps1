# Compiles the project to windows .exe
# sometimes the icon doesnt show up, but thats a windows cahing issue wich can be resolved by just moving the .exe
# https://github.com/pyinstaller/pyinstaller/issues/8784

$MAIN_DIR = "C:\Users\p1geon\Documents\code\music-share"  # change this path
$MAIN_FILE = Join-Path $MAIN_DIR "main.py"
$ASSETS_DIR = Join-Path $MAIN_DIR "assets"
$SCRIPTS_DIR = Join-Path $MAIN_DIR "scripts"
$ICON_FILE = Join-Path $ASSETS_DIR "logo.ico"

# PyInstaller command (same flags, Windows-compatible paths)
pyinstaller --onefile --windowed `
    --icon "$ICON_FILE" `
    --add-data "$ASSETS_DIR;assets" `
    --add-data "$SCRIPTS_DIR;scripts" `
    $MAIN_FILE