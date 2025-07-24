# Antivirus False Positive Solutions

## Why does my antivirus flag the executable?

PyInstaller executables are often flagged by antivirus software as false positives because:
- They contain self-extracting code
- They bundle Python interpreter and libraries
- The binary patterns match some malware signatures

## Solutions:

### 1. Temporary Disable Antivirus (Safest)
- Temporarily disable McAfee real-time protection
- Run the build process
- Add the generated executable to McAfee's exclusion list
- Re-enable real-time protection

### 2. Add Exclusions Before Building
- Add your project folder to McAfee's exclusion list:
  - Open McAfee Security Center
  - Go to Real-Time Scanning settings
  - Add your project directory to excluded folders
  - Add `.exe` files in your project to excluded files

### 3. Alternative Distribution Methods

#### Option A: Use the updated spec file
- The updated spec file creates a directory-based distribution instead of a single file
- This is less likely to trigger antivirus software
- The executable will be in `dist/DocumentToSpeech/DocumentToSpeech.exe`

#### Option B: Create a Python launcher script
- Distribute your Python script with a batch file launcher
- Users install Python and dependencies
- More work for users but avoids antivirus issues

### 4. Code Signing (Professional Solution)
- Purchase a code signing certificate
- Sign your executable with your certificate
- This reduces false positives significantly

## Building with the Updated Configuration

Run the batch file again. The new configuration:
- Disables UPX compression (common trigger)
- Creates a directory distribution instead of single file
- Separates binaries from the main executable

The executable will be in `dist/DocumentToSpeech/` folder with all required files.