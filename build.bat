@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
set "PNG=%ROOT%assets\logo.png"
set "ICO=%ROOT%assets\logo.ico"

if not exist "%PNG%" (
  echo [ERROR] Not found: %PNG%
  exit /b 1
)

echo [1/2] Converting icon: assets\logo.png -^> assets\logo.ico
poetry run python -c "from PIL import Image; im=Image.open(r'%PNG%'); im.save(r'%ICO%', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
if errorlevel 1 (
  echo [ERROR] Icon conversion failed. Ensure dependencies are installed: poetry install
  exit /b 1
)

echo [2/2] Building with PyInstaller
poetry run pyinstaller --noconfirm --clean --windowed --onefile --icon "%ICO%" main.py
if errorlevel 1 (
  echo [ERROR] PyInstaller build failed
  exit /b 1
)

echo [OK] Build finished. See dist\main\main.exe or dist\main.exe depending on PyInstaller mode.
endlocal
