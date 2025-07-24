# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['document_to_speech.py'],
    pathex=[],
    binaries=[
        ('ffmpeg/ffmpeg.exe', '_internal/ffmpeg'),
        ('ffmpeg/ffplay.exe', '_internal/ffmpeg'),
        ('ffmpeg/ffprobe.exe', '_internal/ffmpeg'),
    ],
    datas=[],
    hiddenimports=[
        'pygame',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'docx',
        'PyPDF2',
        'openai',
        'dotenv',
        'tempfile',
        'shutil',
        'uuid',
        'datetime',
        'threading',
        'time',
        'subprocess',
        'sys',
        'urllib.request',
        'zipfile',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DocumentToSpeech',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression to avoid AV detection
    console=False,  # Set to False for windowed app, True for console app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='document_to_speech.ico',  # Icon file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DocumentToSpeech'
)