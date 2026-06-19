# PyInstaller spec - build nhe nhat co the.
# Chay tren Windows: pyinstaller build_exe.spec
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Loai bo cac module nang khong dung den (matplotlib khong con la dependency,
# nhung mot so thu vien (ezdxf, pymupdf) co the keo theo numpy/PIL/qt khong can thiet).
EXCLUDES = [
    "matplotlib",
    "scipy",
    "pandas",
    "PyQt5", "PyQt6", "PySide2", "PySide6",
    "IPython", "jupyter",
    "test", "unittest",
    "tkinter.test",
    "PIL.ImageQt",
]

a = Analysis(
    ["dwg_to_pdf_gui.py"],
    pathex=[],
    binaries=[],
    datas=[("fonts/iso3098.lff", "fonts")],
    hiddenimports=[],
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
    name="DWG_to_PDF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
