@echo off
REM Build file exe nhe nhat tu dwg_sorter_gui.py
REM Chay file nay tren Windows, trong thu muc du an

pip install pyinstaller tkinterdnd2

pyinstaller --noconfirm --clean build_sorter_exe.spec

echo.
echo Xong! File exe nam tai: dist\DWG_Sorter.exe
pause
