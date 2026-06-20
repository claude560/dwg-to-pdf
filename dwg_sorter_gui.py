#!/usr/bin/env python3
"""Tool sap xep file DWG vao thu muc con theo ma loai cau kien.

Tac gia : Le Chi Tam - Mp : 0918 785 009 - lct@luckysteel.vn

Cach dung:
    - Chon thu muc D1 (nut "Chon thu muc") hoac keo tha thu muc vao cua so.
    - Voi moi file ten dang  A-xxx_yyyzzz - REV bb.dwg, lay 3 ky tu "yyy"
      lien ke ngay sau dau "_" de quyet dinh thu muc dich.
    - Move file vao thu muc con tuong ung (tao thu muc neu chua co).
    - Bao cao: cac thu muc duoc tao, so file dwg trong moi thu muc.

Cai dat (tuy chon, de keo tha):  pip install tkinterdnd2
"""
import os
import re
import shutil
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

AUTHOR = "Le Chi Tam - Mp : 0918 785 009 - lct@luckysteel.vn"

# Map ma "yyy" -> ten thu muc dich. Nhieu ma co the tro ve cung 1 thu muc.
CODE_TO_FOLDER = {
    "1BE": "Bend clip",
    "1BK": "Bracket",
    "1CA": "Canopy", "2CA": "Canopy",
    "1CL": "Column", "2CL": "Column",
    "1CB": "Crane beam",
    "1FA": "Fascia",
    "1JB": "Jack beam",
    "1MJ": "Mezz joist", "2MJ": "Mezz joist",
    "1MB": "Mezz beam", "2MB": "Mezz beam",
    "1PL": "Loose part", "1LP": "Loose part", "2LP": "Loose part",
    "1RF": "Rafter", "2RF": "Rafter",
    "1ST": "Strut tube", "2ST": "Strut tube",
    "1VB": "V brace", "2VB": "V brace",
    "1RM": "Roof monitor", "2RM": "Roof monitor",
    "2SS": "Stringer",
    "1LD": "Ladder", "2LD": "Ladder",
}

# Lay 3 ky tu ngay sau dau "_" dau tien.
CODE_RE = re.compile(r"_(...)")


def extract_code(filename: str) -> str | None:
    """Tra ve 3 ky tu "yyy" ngay sau dau '_' dau tien, hoac None neu khong khop."""
    stem = Path(filename).stem
    m = CODE_RE.search(stem)
    if not m:
        return None
    return m.group(1).upper()


def sort_folder(d1: Path, log) -> dict:
    """Move tat ca file .dwg truc tiep trong d1 vao thu muc con theo ma loai.

    Tra ve dict: ten_thu_muc -> so file da move.
    """
    dwg_files = [p for p in d1.iterdir()
                 if p.is_file() and p.suffix.lower() == ".dwg"]
    if not dwg_files:
        raise RuntimeError(f"Khong co file DWG nao truc tiep trong '{d1}'")

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

    # Bao cao
    log("=" * 50)
    log(f"Thu muc xu ly: {d1}")
    log(f"Tong so file DWG: {len(dwg_files)}")
    log("-" * 50)
    if created_folders:
        log(f"Thu muc duoc TAO MOI ({len(created_folders)}): "
            + ", ".join(sorted(created_folders)))
    else:
        log("Khong co thu muc moi (tat ca da ton tai).")
    log("-" * 50)
    log("Ket qua theo thu muc:")
    total_moved = 0
    for folder_name in sorted(moved):
        log(f"  {folder_name:<14}: {moved[folder_name]} file")
        total_moved += moved[folder_name]
    log("-" * 50)
    log(f"Tong cong da move: {total_moved} file")
    if skipped:
        log(f"BO QUA {len(skipped)} file (khong nhan dien duoc ma):")
        for name, code in skipped:
            log(f"  '{name}'  (ma doc duoc: {code})")
    log("=" * 50)
    return dict(moved)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Sap xep file DWG theo loai cau kien")
        root.geometry("680x560")

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Button(top, text="Chon thu muc...", command=self.browse).pack(side="left")
        self.folder_var = tk.StringVar(value="(chua chon thu muc)")
        ttk.Label(top, textvariable=self.folder_var, foreground="blue").pack(
            side="left", padx=10)

        drop_text = ("Keo tha thu muc D1 vao day"
                     if HAS_DND else
                     "Cai 'tkinterdnd2' de keo tha, hoac dung nut Chon thu muc")
        self.drop = tk.Label(root, text=drop_text, relief="ridge", bd=2,
                             height=4, bg="#eef", fg="#333")
        self.drop.pack(fill="x", padx=10, pady=8)
        if HAS_DND:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self.on_drop)

        self.run_btn = ttk.Button(root, text="CHAY SAP XEP", command=self.run)
        self.run_btn.pack(pady=4)

        self.log_box = scrolledtext.ScrolledText(root, height=20, font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=6)

        ttk.Label(root, text="Tac gia: " + AUTHOR, foreground="#555").pack(pady=4)

        self.folder = None

    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def browse(self):
        path = filedialog.askdirectory(title="Chon thu muc D1")
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
            messagebox.showwarning("Loi", "Vui long tha mot THU MUC.")

    def set_folder(self, path: Path):
        self.folder = path
        self.folder_var.set(str(path))

    def run(self):
        if not self.folder:
            messagebox.showwarning("Thieu thu muc", "Hay chon hoac keo tha thu muc D1.")
            return
        self.run_btn.config(state="disabled")
        self.log_box.delete("1.0", "end")
        threading.Thread(target=self._run_thread, daemon=True).start()

    def _run_thread(self):
        try:
            sort_folder(self.folder, self.log)
            self.log("\nHOAN TAT.")
        except Exception as e:
            self.log(f"\nLOI: {e}")
            messagebox.showerror("Loi", str(e))
        finally:
            self.run_btn.config(state="normal")


def main():
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
