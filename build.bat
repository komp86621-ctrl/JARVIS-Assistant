@echo off
chcp 65001 > nul
title JARVIS Builder
color 0B

echo ============================================
echo   СБОРКА JARVIS
echo ============================================
echo.

echo [1/4] Проверка структуры...
if not exist "jarvis.py" (
    echo ОШИБКА: jarvis.py не найден!
    pause
    exit /b 1
)
if not exist "vosk-model-small-ru-0.22" (
    echo ОШИБКА: папка vosk-model-small-ru-0.22 не найдена!
    pause
    exit /b 1
)
if not exist "tesseract\tesseract.exe" (
    echo ПРЕДУПРЕЖДЕНИЕ: tesseract не найден, OCR будет отключён.
)
if not exist "icon.ico" (
    echo ПРЕДУПРЕЖДЕНИЕ: icon.ico не найден, будет стандартная иконка.
)
echo OK.
echo.

echo [2/4] Установка зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo ОШИБКА установки зависимостей!
    pause
    exit /b 1
)
echo.

echo [3/4] Очистка старых сборок...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

echo [4/4] Сборка EXE...
pyinstaller --clean jarvis.spec
if errorlevel 1 (
    echo ОШИБКА сборки!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   ГОТОВО!
echo ============================================
echo.
echo EXE: dist\JARVIS.exe
echo.
dir dist
echo.
pause