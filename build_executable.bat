@echo off
echo Building Windows executable for Document to Speech...
echo.

REM Install all required dependencies
echo Installing required dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install some dependencies. Continuing...
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller. Please install it manually.
        pause
        exit /b 1
    )
)

REM Install Pillow if needed for icon creation
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo Installing Pillow for icon creation...
    pip install Pillow
)

REM Create icon if it doesn't exist
if not exist "document_to_speech.ico" (
    echo Creating application icon...
    python create_icon.py
    if errorlevel 1 (
        echo Pillow not available, creating simple icon...
        python simple_icon.py
        if errorlevel 1 (
            echo Warning: Could not create icon. Continuing without icon...
        )
    )
)

REM Clean up any locked build files
if exist "build" (
    echo Cleaning build directory...
    rmdir /s /q "build" 2>nul
)
if exist "dist" (
    echo Cleaning dist directory... 
    rmdir /s /q "dist" 2>nul
)

REM Build the executable
echo Building executable...
python -m PyInstaller --clean document_to_speech.spec

if errorlevel 1 (
    echo Build failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable can be found in the 'dist' folder.
echo.
pause