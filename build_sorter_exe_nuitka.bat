@echo off
REM Build DWG_Sorter.exe bang Nuitka (bien dich ra C/C++ thuc su, kho dich
REM nguoc hon nhieu so voi PyInstaller - vi PyInstaller chi dong goi bytecode
REM .pyc, con Nuitka bien dich code Python thanh C roi compile thanh may
REM binary native).
REM
REM Chay file nay tren Windows, trong thu muc du an. Lan dau se cham hon
REM PyInstaller (Nuitka can trinh bien dich C - se tu dong tai MinGW64 neu
REM chua co, hoi xac nhan thi nhan Y/Enter).
REM
REM Can Nuitka >= 1.9 (co flag --windows-console-mode). Neu ban dang dung
REM ban cu hon, doi flag "--windows-console-mode=disable" thanh
REM "--windows-disable-console".

pip install nuitka tkinterdnd2

python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-plugin=tk-inter ^
    --windows-console-mode=disable ^
    --include-package=licensing ^
    --include-package-data=tkinterdnd2 ^
    --nofollow-import-to=ezdxf,pymupdf,fitz,pypdf,openpyxl,numpy,matplotlib,scipy,pandas,PIL,PyQt5,PyQt6,PySide2,PySide6,IPython,jupyter ^
    --output-dir=dist ^
    --output-filename=DWG_Sorter.exe ^
    --remove-output ^
    dwg_sorter_gui.py

echo.
echo Xong! File exe nam tai: dist\DWG_Sorter.exe
echo.
echo QUAN TRONG: Phai chep file license.lic vao CUNG thu muc voi DWG_Sorter.exe
echo (xem licensing\license_admin.py de tao file license.lic).
pause
