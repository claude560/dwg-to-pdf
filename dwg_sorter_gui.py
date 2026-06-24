#!/usr/bin/env python3
"""Tool sap xep file DWG vao thu muc con theo ma loai cau kien.

Tac gia : Le Chi Tam - Mp : 0918 785 009 - lct@luckysteel.vn

Cach dung:
    - Chon thu muc D1 (nut "Chon thu muc") hoac keo tha thu muc vao cua so.
    - Voi moi file ten dang  A-xxx_yyyzzz - REV bb.dwg, lay chuoi nam giua
      dau "_" va dau "-" ke tiep, bo het ky tu so (0-9), chi giu ky tu chu
      (string) -> goi la "yyy", dung de quyet dinh thu muc dich.
    - Move file vao thu muc con tuong ung (tao thu muc neu chua co).
    - Bao cao: cac thu muc duoc tao, so file dwg trong moi thu muc.

Cai dat (tuy chon, de keo tha):  pip install tkinterdnd2
"""
import os
import re
import shutil
import sys
import threading
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

sys.path.insert(0, str(Path(__file__).resolve().parent))
from licensing.license_core import check_license  # noqa: E402
from licensing.machine_id import get_machine_id  # noqa: E402

AUTHOR = "Lê Chí Tâm - Mp : 0918 785 009 - lct@luckysteel.vn"

def _license_search_dirs() -> list[Path]:
    """Cac thu muc co the chua license.lic, theo thu tu uu tien.

    Voi Nuitka onefile, sys.executable / __file__ co the tro vao thu muc TAM
    luc giai nen, khong phai thu muc chua DWG_Sorter.exe that. sys.argv[0]
    moi tro dung file exe nguoi dung bam chay -> uu tien no. Them cwd va cac
    duong dan khac de chac chan tim ra file ke ben exe.
    """
    dirs: list[Path] = []

    def _add(p: Path) -> None:
        try:
            rp = p.resolve()
        except Exception:
            return
        if rp not in dirs:
            dirs.append(rp)

    # 1. Thu muc chua file exe nguoi dung bam chay (dung nhat cho onefile).
    if sys.argv and sys.argv[0]:
        _add(Path(sys.argv[0]).parent)
    # 2. Thu muc chua binary (PyInstaller, hoac Nuitka standalone).
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        _add(Path(sys.executable).parent)
    # 3. Thu muc nguon (khi chay truc tiep .py).
    _add(Path(__file__).parent)
    # 4. Thu muc lam viec hien hanh.
    _add(Path.cwd())
    return dirs


def _find_license() -> Path:
    """Tra ve duong dan license.lic dau tien ton tai; neu khong co, tra ve
    ung vien dau tien (de thong bao loi hien duong dan hop ly)."""
    candidates = [d / "license.lic" for d in _license_search_dirs()]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


LICENSE_PATH = _find_license()

# Map ma "yyy" (chi gom ky tu chu, da bo so) -> ten thu muc dich.
CODE_TO_FOLDER = {
    "BE": "BEND CLIP",
    "BK": "BRACKET",
    "CA": "CANOPY",
    "CL": "COLUMN",
    "CB": "CRANE BEAM",
    "FA": "FASCIA",
    "JB": "JACK BEAM",
    "MJ": "MEZZ JOIST",
    "MB": "MEZZ BEAM",
    "PL": "LOOSE PART", "LP": "LOOSE PART",
    "RF": "RAFTER",
    "ST": "STRUT TUBE",
    "VB": "V BRACE",
    "RM": "ROOF MONITOR",
    "SS": "STRINGER",
    "LD": "LADDER",
    "SB": "STRUT BEAM",
    "F": "FLANGE",
    "H": "HOT-ROLL", "L": "HOT-ROLL", "V": "HOT-ROLL",
    "T": "HOT-ROLL", "U": "HOT-ROLL", "P": "HOT-ROLL",
    "E": "PLATE", "EH": "PLATE", "S": "PLATE", "SH": "PLATE", "BP": "PLATE",
    "W": "WEB", "WT": "WEB", "WC": "WEB",
    "CK": "CHECKER",
    "PU": "PURLIN",
    "GT": "GIRT",
    "SA": "BEND GALVANISE", "AS": "BEND GALVANISE",
    "AC": "BEND GALVANISE", "BG": "BEND GALVANISE",
}

# Chuoi nam giua dau "_" dau tien va dau "-" ke tiep.
CODE_RE = re.compile(r"_([^-]*)-")


def extract_code(filename: str) -> str | None:
    """Tra ve "yyy": chuoi giua '_' va '-' ke tiep, sau khi bo het ky tu so.

    Vd "A-101_1BE001 - REV 00.dwg" -> phan giua la "1BE001 " -> bo so -> "BE".
    Tra ve None neu khong tim thay dau '_'/'-' theo dung thu tu, hoac phan
    con lai sau khi bo so la rong.
    """
    m = CODE_RE.search(filename)
    if not m:
        return None
    letters_only = re.sub(r"[0-9]", "", m.group(1)).strip()
    return letters_only.upper() if letters_only else None


def sort_folder(d1: Path, log) -> dict:
    """Move tat ca file .dwg truc tiep trong d1 vao thu muc con theo ma loai.

    Tra ve dict: ten_thu_muc -> so file da move.
    """
    dwg_files = [p for p in d1.iterdir()
                 if p.is_file() and p.suffix.lower() == ".dwg"]
    if not dwg_files:
        raise RuntimeError(f"Không có file DWG nào trực tiếp trong '{d1}'")

    moved = defaultdict(int)
    created_folders = set()
    skipped = []

    for f in dwg_files:
        code = extract_code(f.name)
        folder_name = CODE_TO_FOLDER.get(code) if code else None
        if not folder_name:
            skipped.append((f.name, code))
            continue

        dest_dir = d1 / folder_name
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            created_folders.add(folder_name)

        dest = dest_dir / f.name
        # Neu trung ten, them hau to _1, _2...
        if dest.exists():
            i = 1
            while True:
                alt = dest_dir / f"{f.stem}_{i}{f.suffix}"
                if not alt.exists():
                    dest = alt
                    break
                i += 1
        shutil.move(str(f), str(dest))
        moved[folder_name] += 1

    # Báo cáo
    log("=" * 50)
    log(f"Thư mục xử lý: {d1}")
    log(f"Tổng số file DWG: {len(dwg_files)}")
    log("-" * 50)
    if created_folders:
        log(f"Thư mục được TẠO MỚI ({len(created_folders)}): "
            + ", ".join(sorted(created_folders)))
    else:
        log("Không có thư mục mới (tất cả đã tồn tại).")
    log("-" * 50)
    log("Kết quả theo thư mục:")
    total_moved = 0
    for folder_name in sorted(moved):
        log(f"  {folder_name:<18}: {moved[folder_name]} file")
        total_moved += moved[folder_name]
    log("-" * 50)
    log(f"Tổng cộng đã chuyển: {total_moved} file")
    if skipped:
        log(f"BỎ QUA {len(skipped)} file (không nhận diện được mã):")
        for name, code in skipped:
            log(f"  '{name}'  (mã đọc được: {code})")
    log("=" * 50)
    return dict(moved)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Sắp xếp file DWG theo loại cấu kiện")
        root.geometry("680x560")

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Button(top, text="Chọn thư mục...", command=self.browse).pack(side="left")
        self.folder_var = tk.StringVar(value="(chưa chọn thư mục)")
        ttk.Label(top, textvariable=self.folder_var, foreground="blue").pack(
            side="left", padx=10)

        drop_text = ("Kéo thả thư mục D1 vào đây"
                     if HAS_DND else
                     "Cài 'tkinterdnd2' để kéo thả, hoặc dùng nút Chọn thư mục")
        self.drop = tk.Label(root, text=drop_text, relief="ridge", bd=2,
                             height=4, bg="#eef", fg="#333")
        self.drop.pack(fill="x", padx=10, pady=8)
        if HAS_DND:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self.on_drop)

        self.run_btn = ttk.Button(root, text="CHẠY SẮP XẾP", command=self.run)
        self.run_btn.pack(pady=4)

        self.log_box = scrolledtext.ScrolledText(root, height=20, font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=6)

        ttk.Label(root, text="Tác giả: " + AUTHOR, foreground="#555").pack(pady=4)

        self.folder = None

    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def browse(self):
        path = filedialog.askdirectory(title="Chọn thư mục D1")
        if path:
            self.set_folder(Path(path))

    def on_drop(self, event):
        raw = event.data.strip()
        # tkinterdnd2 boc duong dan co khoang trang trong dau {}
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        path = Path(raw)
        if path.is_dir():
            self.set_folder(path)
        else:
            messagebox.showwarning("Lỗi", "Vui lòng thả một THƯ MỤC.")

    def set_folder(self, path: Path):
        self.folder = path
        self.folder_var.set(str(path))

    def run(self):
        if not self.folder:
            messagebox.showwarning("Thiếu thư mục", "Hãy chọn hoặc kéo thả thư mục D1.")
            return
        self.run_btn.config(state="disabled")
        self.log_box.delete("1.0", "end")
        threading.Thread(target=self._run_thread, daemon=True).start()

    def _run_thread(self):
        try:
            sort_folder(self.folder, self.log)
            self.log("\nHOÀN TẤT.")
        except Exception as e:
            self.log(f"\nLỖI: {e}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            self.run_btn.config(state="normal")


def main():
    machine_id = get_machine_id()
    ok, msg = check_license(LICENSE_PATH, machine_id)
    if not ok:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Khong the chay phan mem", msg)
        root.destroy()
        sys.exit(1)

    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
