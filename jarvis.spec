# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs
import os

datas = [
    ('vosk-model-small-ru-0.22', 'vosk-model-small-ru-0.22'),
    ('tesseract', 'tesseract'),
]
if os.path.exists('ffmpeg/ffmpeg.exe'):
    datas.append(('ffmpeg/ffmpeg.exe', 'ffmpeg'))
if os.path.exists('icon.ico'):
    datas.append(('icon.ico', '.'))

datas += collect_data_files('mediapipe')
datas += collect_data_files('edge_tts')
datas += collect_data_files('vosk')
datas += collect_data_files('speech_recognition')
datas += collect_data_files('setuptools')
datas += collect_data_files('gtts')

binaries = []
binaries += collect_dynamic_libs('pyaudio')
binaries += collect_dynamic_libs('vosk')
binaries += collect_dynamic_libs('mediapipe')
binaries += collect_dynamic_libs('cv2')
binaries += collect_dynamic_libs('numpy')

hiddenimports = [
    'pyaudio', 'vosk', 'edge_tts', 'mediapipe', 'cv2', 'numpy',
    'mutagen', 'mutagen.mp3', 'psutil', 'pyperclip',
    'speech_recognition', 'deep_translator', 'pytesseract',
    'PIL', 'PIL.Image', 'PIL.ImageGrab',
    'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'speedtest', 'secrets', 'hashlib', 'asyncio', 'json',
    'urllib.parse', 'ctypes', 'winsound', 'socket', 'zipfile',
    'threading', 'subprocess', 'webbrowser',
    'setuptools',
    'setuptools._distutils',
    'distutils',
    'distutils.util',
    'distutils.spawn',
    'distutils.errors',
    'distutils.version',
    'gtts',
    'gtts.tts',
    'gtts.lang',
]
hiddenimports += collect_submodules('mediapipe')
hiddenimports += collect_submodules('edge_tts')
hiddenimports += collect_submodules('vosk')
hiddenimports += collect_submodules('setuptools')
hiddenimports += collect_submodules('distutils')
hiddenimports += collect_submodules('gtts')

excludes = [
    'matplotlib', 'tkinter', 'scipy', 'pandas',
    'notebook', 'jupyter', 'IPython', 'pytest',
    'pip', 'wheel',
    'pygame', 'torch', 'torchvision', 'torchaudio',
    'torch.utils', 'torch.utils.tensorboard',
    'tensorboard', 'tensorflow',
    'pyttsx3', 'comtypes', 'win32com',
]

a = Analysis(
    ['jarvis.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='JARVIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python3.dll', 'tesseract.exe', 'ffmpeg.exe'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)