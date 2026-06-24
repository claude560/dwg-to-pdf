@echo off
REM Build exe nho de gui cho NGUOI DUNG CUOI: chi in ra Machine ID cua may ho,
REM khong can cai Python. Chay file nay tren Windows, trong thu muc du an.

pip install pyinstaller

pyinstaller --noconfirm --clean --onefile --console --name MachineID licensing\machine_id.py

echo.
echo Xong! File exe nam tai: dist\MachineID.exe
echo Gui file nay cho nguoi dung cuoi - ho chay len se thay Machine ID cua may.
pause
