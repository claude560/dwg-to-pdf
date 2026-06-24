# PyInstaller spec - build exe nhe nhat cho dwg_sorter_gui.py
# Chay tren Windows: pyinstaller build_sorter_exe.spec
#
# Tool nay chi dung tkinter (san trong Python) + tkinterdnd2 (de keo tha),
# nen exe rat nho. Loai bo cac thu vien nang khong lien quan.

block_cipher = None

EXCLUDES = [
    "ezdxf", "pymupdf", "fitz", "pypdf", "openpyxl",
    "numpy", "matplotlib", "scipy", "pandas", "PIL",
    "PyQt5", "PyQt6", "PySide2", "PySide6",
    "IPython", "jupyter",
]

a = Analysis(
    ["dwg_sorter_gui.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["licensing", "licensing.license_core", "licensing.machine_id"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DWG_Sorter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
