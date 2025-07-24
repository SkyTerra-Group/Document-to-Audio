"""
Enhanced ffmpeg setup that ensures ffmpeg is available for both development and executable
"""
import os
import sys
import shutil
import urllib.request
import zipfile
import tempfile

def download_ffmpeg():
    """Download ffmpeg to local directory"""
    print("Downloading ffmpeg...")
    
    try:
        # Create ffmpeg directory in current folder
        ffmpeg_dir = os.path.join(os.getcwd(), 'ffmpeg')
        os.makedirs(ffmpeg_dir, exist_ok=True)
        
        # Check if already exists
        ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_exe):
            print("ffmpeg already exists in local directory")
            return True
        
        # Download URL
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            
            print("Downloading from GitHub...")
            urllib.request.urlretrieve(url, zip_path)
            
            print("Extracting ffmpeg...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find and copy ffmpeg binaries
            for root, dirs, files in os.walk(temp_dir):
                if 'bin' in dirs:
                    bin_dir = os.path.join(root, 'bin')
                    for file in os.listdir(bin_dir):
                        if file.endswith('.exe'):
                            src = os.path.join(bin_dir, file)
                            dst = os.path.join(ffmpeg_dir, file)
                            shutil.copy2(src, dst)
                            print(f"Copied {file}")
        
        return True
        
    except Exception as e:
        print(f"Failed to download ffmpeg: {e}")
        return False

def main():
    """Setup ffmpeg for the application"""
    # First check if ffmpeg is in PATH
    if shutil.which("ffmpeg"):
        print("ffmpeg found in system PATH")
        return True
    
    # Check local ffmpeg directory
    local_ffmpeg = os.path.join(os.getcwd(), 'ffmpeg', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        print("ffmpeg found in local directory")
        return True
    
    # Download ffmpeg
    if download_ffmpeg():
        print("ffmpeg setup completed successfully")
        return True
    else:
        print("ffmpeg setup failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)