"""
Automatic ffmpeg installer for Windows
"""
import os
import sys
import shutil
import urllib.request
import zipfile
import tempfile

def install_ffmpeg_windows():
    """Download and install ffmpeg binaries for Windows"""
    
    # Check if ffmpeg is already available
    if shutil.which("ffmpeg"):
        print("ffmpeg is already installed and available in PATH")
        return True
    
    # Check if ffmpeg exists in local directory
    local_ffmpeg = os.path.join(os.getcwd(), 'ffmpeg', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        print("ffmpeg found in local directory")
        # Add to PATH
        ffmpeg_dir = os.path.dirname(local_ffmpeg)
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        return True
    
    print("Downloading ffmpeg...")
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download ffmpeg
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            
            print("Downloading from GitHub...")
            urllib.request.urlretrieve(url, zip_path)
            
            print("Extracting ffmpeg...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the ffmpeg binaries and copy them
            ffmpeg_dir = os.path.join(os.getcwd(), 'ffmpeg')
            os.makedirs(ffmpeg_dir, exist_ok=True)
            
            for root, dirs, files in os.walk(temp_dir):
                if 'bin' in dirs:
                    bin_dir = os.path.join(root, 'bin')
                    for file in os.listdir(bin_dir):
                        if file.endswith('.exe'):
                            src = os.path.join(bin_dir, file)
                            dst = os.path.join(ffmpeg_dir, file)
                            shutil.copy2(src, dst)
                            print(f"Copied {file}")
            
            # Add to PATH for this session
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            
            print("ffmpeg installed successfully!")
            return True
            
    except Exception as e:
        print(f"Failed to install ffmpeg: {e}")
        print("You may need to install ffmpeg manually from https://ffmpeg.org/download.html")
        return False

def main():
    if sys.platform == 'win32':
        install_ffmpeg_windows()
    else:
        print("This script only supports Windows automatic installation.")
        print("On other platforms, please install ffmpeg using your package manager:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")

if __name__ == "__main__":
    main()