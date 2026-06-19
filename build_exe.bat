@echo off
REM Build file exe nhe nhat tu dwg_to_pdf_gui.py
REM Chay file nay tren Windows, trong thu muc du an (co dwg_to_pdf_gui.py va fonts\iso3098.lff)

pip install pyinstaller tkinterdnd2 pypdf ezdxf pymupdf

pyinstaller --noconfirm --clean build_exe.spec

echo.
echo Xong! File exe nam tai: dist\DWG_to_PDF.exe
pause
