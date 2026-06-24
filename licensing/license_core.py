"""Tao/kiem tra file license.lic (gioi han may su dung + ngay het han).

File license.lic la JSON co ky (HMAC-SHA256) bang 1 secret key nhung trong
code nay - chong sua tay file (sua xong se sai chu ky -> bi tu choi). Day la
bao ve o muc co ban, du dung cho noi bo cong ty; khong chong duoc nguoi am
hieu ky thuat dich nguoc file .exe de lay secret key.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import date
from pathlib import Path

# Secret key dung de ky/xac thuc license. PHAI giong nhau giua license_admin.py
# va ung dung (dwg_sorter_gui.py). Doi cac manh _K1.._K5 nay neu muon "reset"
# toan bo license cu da phat hanh (vd lo secret). Chia nho + dao thu tu khi
# ghep, de khong hien thanh 1 chuoi ro nghia khi mo file .exe bang text editor.
_K1 = b"kS9p"
_K2 = b"-Lu"
_K3 = b"ckySte"
_K4 = b"el-PEB-"
_K5 = b"x7Qz2026!"
SECRET_KEY = _K3 + _K1 + _K2 + _K5 + _K4[::-1]


def _canonical(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sign(data: dict) -> str:
    return hmac.new(SECRET_KEY, _canonical(data), hashlib.sha256).hexdigest()


def build_license(allowed_ids: list[str], expiry: str, note: str = "") -> dict:
    """allowed_ids: list Machine ID (xem licensing/machine_id.py).
    expiry: 'YYYY-MM-DD' - ngay cuoi cung con duoc dung (bao gom ngay nay)."""
    data = {
        "allowed_ids": sorted({m.strip().upper() for m in allowed_ids if m.strip()}),
        "expiry": expiry,
        "note": note,
    }
    return {"data": data, "signature": _sign(data)}


def save_license(path: Path, allowed_ids: list[str], expiry: str, note: str = "") -> None:
    license_obj = build_license(allowed_ids, expiry, note)
    path.write_text(json.dumps(license_obj, indent=2, ensure_ascii=False), encoding="utf-8")


def check_license(path: Path, machine_id: str) -> tuple[bool, str]:
    """Tra ve (hop_le, thong_bao)."""
    if not path.exists():
        return False, (
            "Khong tim thay file license.lic.\n"
            f"Machine ID cua may nay: {machine_id}\n"
            "Hay gui Machine ID nay cho quan tri vien de duoc cap quyen."
        )

    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        data = obj["data"]
        signature = obj["signature"]
    except Exception:
        return False, "File license.lic bi loi hoac sai dinh dang."

    expected_sig = _sign(data)
    if not hmac.compare_digest(expected_sig, signature):
        return False, "File license.lic khong hop le (da bi sua doi)."

    try:
        expiry_date = date.fromisoformat(data["expiry"])
    except Exception:
        return False, "File license.lic co ngay het han khong hop le."

    if date.today() > expiry_date:
        return False, f"License da HET HAN ngay {data['expiry']}. Vui long lien he quan tri vien."

    allowed_ids = set(data.get("allowed_ids", []))
    if machine_id.upper() not in allowed_ids:
        return False, (
            f"May nay CHUA DUOC CAP QUYEN su dung phan mem.\n"
            f"Machine ID cua may nay: {machine_id}\n"
            "Hay gui Machine ID nay cho quan tri vien de duoc cap quyen."
        )

    return True, f"Hop le den het ngay {data['expiry']}."
