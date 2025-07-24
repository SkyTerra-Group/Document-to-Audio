@echo off
echo Testing ffmpeg setup...
echo.

REM Run the ffmpeg setup
python setup_ffmpeg.py

echo.
echo Checking if ffmpeg is accessible...
python -c "import shutil; print('✓ ffmpeg found' if shutil.which('ffmpeg') else '✗ ffmpeg not in PATH')"

echo.
echo Checking local ffmpeg directory...
if exist "ffmpeg\ffmpeg.exe" (
    echo ✓ ffmpeg.exe found in local directory
    ffmpeg\ffmpeg.exe -version | findstr "ffmpeg version"
) else (
    echo ✗ ffmpeg.exe not found in local directory
)

echo.
pause