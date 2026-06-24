"""Lay 'Machine ID' duy nhat cho 1 may Windows, dung lam khoa gioi han license.

Ket hop serial mainboard + serial o cung (disk dau tien) -> hash SHA-256,
rut gon thanh chuoi de doc/copy. Khong can quyen admin de doc cac gia tri nay.
"""
from __future__ import annotations

import hashlib
import subprocess
import uuid


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return out.strip()
    except Exception:
        return ""


def _parse_wmic_value(output: str) -> str:
    """wmic in 2 dong: ten cot, roi gia tri. Lay dong khong rong thu 2."""
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    return lines[1] if len(lines) >= 2 else ""


def _get_baseboard_serial() -> str:
    val = _parse_wmic_value(_run(["wmic", "baseboard", "get", "serialnumber"]))
    if val and val.lower() not in ("", "default string", "none", "to be filled by o.e.m."):
        return val
    val = _run([
        "powershell", "-NoProfile", "-Command",
        "(Get-CimInstance Win32_BaseBoard).SerialNumber",
    ])
    return val


def _get_disk_serial() -> str:
    val = _parse_wmic_value(_run(["wmic", "diskdrive", "get", "serialnumber"]))
    if val:
        return val
    val = _run([
        "powershell", "-NoProfile", "-Command",
        "(Get-CimInstance Win32_DiskDrive | Select-Object -First 1).SerialNumber",
    ])
    return val


def get_machine_id() -> str:
    """Tra ve Machine ID dang 'XXXX-XXXX-XXXX-XXXX' (16 hex ky tu, viet hoa).

    Tren Windows: hash(serial_mainboard + serial_o_cung).
    Tren may khong lay duoc 2 gia tri tren (vd khong phai Windows, hoac may
    ao chan WMI): fallback dung dia chi MAC (it tin cay hon, chi de test).
    """
    baseboard = _get_baseboard_serial()
    disk = _get_disk_serial()
    raw = f"{baseboard}|{disk}"
    if not baseboard and not disk:
        raw = f"MAC|{uuid.getnode()}"

    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()
    return "-".join(digest[i:i + 4] for i in range(0, 16, 4))


if __name__ == "__main__":
    mid = get_machine_id()
    print("=" * 50)
    print("MACHINE ID cua may nay la:")
    print()
    print(f"    {mid}")
    print()
    print("Gui ma nay cho quan tri vien de duoc cap quyen su dung phan mem.")
    print("=" * 50)
    input("Nhan Enter de dong...")
