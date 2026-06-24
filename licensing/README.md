# Licensing - huong dan cho ADMIN (Le Chi Tam)

He thong gioi han: so may duoc dung (theo Machine ID = hash serial mainboard +
serial o cung) va thoi han su dung (ngay het han). Ap dung cho `dwg_sorter_gui.py`.

## Quy trinh cap quyen cho 1 may moi

1. Gui cho nguoi dung file `MachineID.exe` (build tu `build_machine_id_exe.bat`)
   hoac huong dan ho chay `python licensing/machine_id.py`.
2. Nguoi dung chay len, gui lai cho ban day Machine ID dang
   `XXXX-XXXX-XXXX-XXXX`.
3. Chay `python licensing/license_admin.py`, nhap duong dan `license.lic` hien
   tai (neu da co, se duoc giu lai cac ID cu), them Machine ID moi, nhap ngay
   het han, ghi chu.
4. Gui file `license.lic` vua tao cho nguoi dung, yeu cau chep vao **CUNG thu
   muc** voi `DWG_Sorter.exe`.

## Build exe (chong dich nguoc)

Dung `build_sorter_exe_nuitka.bat` (khong dung `build_sorter_exe.bat` -
PyInstaller - nua) de build `DWG_Sorter.exe`. Nuitka bien dich code Python
(gom ca phan kiem tra license) thanh C/C++ roi compile ra may binary thuc su,
kho dich nguoc lai ra source hon nhieu so voi PyInstaller (PyInstaller chi
dong goi nguyen file `.pyc`, de decompile bang cong cu nhu `uncompyle6`).

Lan build dau co the cham va se tu dong tai trinh bien dich C (MinGW64) neu
may chua co - cu xac nhan Y/Enter khi duoc hoi.

## Luu y

- `license.lic` KHONG duoc dong goi vao file exe - de co the cap/sua quyen ma
  khong can build lai exe.
- Khong gui `license_admin.py` hay `SECRET_KEY` (trong `license_core.py`) cho
  nguoi dung cuoi.
- Muon "reset" toan bo license da phat hanh (vd lo SECRET_KEY): doi gia tri
  `SECRET_KEY` trong `license_core.py`, build lai exe, tao lai `license.lic`
  moi cho tat ca may.
