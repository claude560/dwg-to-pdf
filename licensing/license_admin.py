#!/usr/bin/env python3
"""Cong cu ADMIN: tao/cap nhat file license.lic cho cac tool noi bo.

CHI dung cho quan tri vien (Le Chi Tam). KHONG gui file nay cho nguoi dung
cuoi - chi gui file license.lic da tao ra.

Cach dung:
    python licensing/license_admin.py

Roi nhap:
    - Danh sach Machine ID duoc phep (lay tu licensing/machine_id.py chay
      tren tung may can cap quyen), moi ID 1 dong, dong rong de ket thuc.
    - Ngay het han (YYYY-MM-DD).
    - Duong dan luu file license.lic (Enter de dung "license.lic" trong
      thu muc hien tai).
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from licensing.license_core import save_license, check_license  # noqa: E402


def read_ids() -> list[str]:
    print("Nhap Machine ID duoc phep, moi ID 1 dong (dong rong de ket thuc):")
    ids = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        ids.append(line)
    return ids


def read_expiry() -> str:
    default = (date.today() + timedelta(days=365)).isoformat()
    raw = input(f"Ngay het han (YYYY-MM-DD) [Enter = {default}]: ").strip()
    return raw or default


def main():
    print("=" * 60)
    print("TAO / CAP NHAT FILE LICENSE.LIC")
    print("=" * 60)

    existing_path = input("Duong dan file license.lic [Enter = ./license.lic]: ").strip()
    out_path = Path(existing_path) if existing_path else Path("license.lic")
    if out_path.is_dir():
        out_path = out_path / "license.lic"

    existing_ids = []
    if out_path.exists():
        import json
        try:
            obj = json.loads(out_path.read_text(encoding="utf-8"))
            existing_ids = obj["data"].get("allowed_ids", [])
            print(f"\nFile da co {len(existing_ids)} Machine ID:")
            for m in existing_ids:
                print(f"  - {m}")
            keep = input("\nGiu lai cac ID nay va THEM ID moi? (Y/n): ").strip().lower()
            if keep == "n":
                existing_ids = []
        except Exception:
            print("(Khong doc duoc file cu, se tao file moi.)")

    print()
    new_ids = read_ids()
    all_ids = list(dict.fromkeys(existing_ids + new_ids))  # giu thu tu, bo trung

    if not all_ids:
        print("Chua co Machine ID nao - huy.")
        return

    expiry = read_expiry()
    note = input("Ghi chu (tuy chon, vd ten cong ty/du an): ").strip()

    save_license(out_path, all_ids, expiry, note)

    print()
    print(f"Da luu: {out_path.resolve()}")
    print(f"Tong so may duoc cap quyen: {len(all_ids)}")
    print(f"Het han: {expiry}")
    ok, msg = check_license(out_path, all_ids[0])
    print(f"Kiem tra lai file vua tao: {'OK' if ok else 'LOI'} - {msg}")
    print()
    print("Copy file nay vao CUNG thu muc voi file .exe cua nguoi dung.")


if __name__ == "__main__":
    main()
