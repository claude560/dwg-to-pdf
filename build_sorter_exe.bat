@echo off
REM Build file exe nhe nhat tu dwg_sorter_gui.py
REM Chay file nay tren Windows, trong thu muc du an
REM
REM (Tuy chon) De exe nho hon ~20-35%% bang UPX:
REM   1. Tai UPX: https://github.com/upx/upx/releases (ban win64)
REM   2. Giai nen, chep upx.exe vao mot thu mục co trong PATH
REM      (hoac them tham so  --upx-dir C:\duong_dan\upx  vao lenh pyinstaller ben duoi)
REM   PyInstaller se tu dong dung UPX neu tim thay. Khong co UPX van build binh thuong.
REM   Luu y: UPX co the bi antivirus bao nham - neu gap, bo UPX (sua upx=True thanh False
REM   trong build_sorter_exe.spec).

pip install pyinstaller tkinterdnd2

pyinstaller --noconfirm --clean build_sorter_exe.spec

echo.
echo Xong! File exe nam tai: dist\DWG_Sorter.exe
echo.
echo QUAN TRONG: Phai chep file license.lic vao CUNG thu muc voi DWG_Sorter.exe
echo (xem licensing\license_admin.py de tao file license.lic).
pause
