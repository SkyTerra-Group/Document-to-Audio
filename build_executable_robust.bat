@echo off
echo Building Windows executable for Document to Speech...
echo.

REM Kill any processes that might be locking files
taskkill /f /im DocumentToSpeech.exe 2>nul

REM Wait a moment for processes to terminate
timeout /t 2 /nobreak >nul

REM Force remove build and dist directories
if exist "build" (
    echo Removing build directory...
    rd /s /q "build" 2>nul
    if exist "build" (
        echo Warning: Could not remove build directory completely
    )
)

if exist "dist" (
    echo Removing dist directory...
    rd /s /q "dist" 2>nul
    if exist "dist" (
        echo Warning: Could not remove dist directory completely
    )
)

REM Install only the essential dependencies needed for the app
echo Installing essential dependencies...
pip install pygame python-docx PyPDF2 openai python-dotenv --quiet --disable-pip-version-check

REM Install ffmpeg-python for easier ffmpeg management
echo Installing ffmpeg support...
pip install ffmpeg-python --quiet --disable-pip-version-check

REM Try to install ffmpeg binaries automatically
echo Checking for ffmpeg installation...
python -c "import shutil; print('ffmpeg found' if shutil.which('ffmpeg') else 'ffmpeg not found')"

REM Setup ffmpeg (download to local directory)
echo Setting up ffmpeg...
python setup_ffmpeg.py
if errorlevel 1 (
    echo Warning: ffmpeg setup failed, continuing anyway...
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller --quiet --disable-pip-version-check
)

REM Create a simple icon without dependencies
if not exist "document_to_speech.ico" (
    echo Creating simple icon...
    python simple_icon.py
    if errorlevel 1 (
        echo Could not create icon, continuing without...
    )
)

REM Build with --noconfirm to avoid interactive prompts
echo Building executable...
python -m PyInstaller --noconfirm --clean document_to_speech.spec

if errorlevel 1 (
    echo Build failed. Trying alternative approach...
    echo.
    echo Trying single-file build without custom spec...
    python -m PyInstaller --noconfirm --onefile --windowed --name "DocumentToSpeech" document_to_speech.py
    if errorlevel 1 (
        echo Alternative build also failed.
        echo.
        echo Trying directory build...
        python -m PyInstaller --noconfirm --onedir --windowed --name "DocumentToSpeech" document_to_speech.py
    )
)

echo.
if exist "dist" (
    echo Build completed! Check the 'dist' folder for your executable.
    dir dist
) else (
    echo Build failed. Please check the error messages above.
)
echo.
pause