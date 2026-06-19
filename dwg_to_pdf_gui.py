#!/usr/bin/env python3
"""GUI tool to batch-convert DWG folders to a single merged PDF per top-level folder.

Workflow:
    - Drag and drop one or more top-level folders onto the window (or use "Chon thu muc").
    - Each top-level folder may contain level-2 / level-3 subfolders holding the .dwg files.
    - Choose paper size and orientation in the settings dialog before running.
    - All .dwg files found anywhere under a top-level folder are converted to PDF and merged
      into a single file named "<ten thu muc cap 1> tong hop.pdf".

Requirements:
    - ODA File Converter installed (https://www.opendesign.com/guestfiles/oda_file_converter)
      -> used only to convert DWG to DXF (ODA does not export PDF directly).
    - pip install tkinterdnd2 pypdf ezdxf pymupdf
"""
import os
import shutil
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.pymupdf import PyMuPdfBackend
from ezdxf.addons.drawing.config import Configuration, ColorPolicy, BackgroundPolicy
from ezdxf.addons.drawing.layout import Page, Margins, Settings, Units
from pypdf import PdfReader, PdfWriter

PAPER_SIZES_MM = {
    "A0": (841, 1189),
    "A1": (594, 841),
    "A2": (420, 594),
    "A3": (297, 420),
    "A4": (210, 297),
    "Letter": (215.9, 279.4),
}


def paper_size_mm(name: str, landscape: bool) -> tuple[float, float]:
    w_mm, h_mm = PAPER_SIZES_MM[name]
    if landscape:
        w_mm, h_mm = max(w_mm, h_mm), min(w_mm, h_mm)
    else:
        w_mm, h_mm = min(w_mm, h_mm), max(w_mm, h_mm)
    return w_mm, h_mm


def find_oda_converter() -> str:
    for name in ("ODAFileConverter", "ODAFileConverter.exe"):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError(
        "Khong tim thay ODA File Converter. Cai dat tu "
        "https://www.opendesign.com/guestfiles/oda_file_converter"
    )


def collect_dwg_files(root_folder: Path) -> list[Path]:
    # set() de tranh trung file tren he thong khong phan biet hoa/thuong (Windows).
    seen = {p.resolve() for p in root_folder.rglob("*.dwg") if p.is_file()}
    seen |= {p.resolve() for p in root_folder.rglob("*.DWG") if p.is_file()}
    return sorted(seen)


def convert_folder_to_dxf(top_folder: Path, output_dir: Path, oda_path: str) -> None:
    """Goi ODA File Converter MOT LAN cho ca thu muc (recurse=1) thay vi tung file,
    vi moi lan khoi dong tien trinh ODA ton vai giay -> goi tung file rat cham."""
    output_dir.mkdir(parents=True, exist_ok=True)
    # Audit=0: bo buoc kiem tra/sua loi tung file -> ODA chay nhanh hon dang ke.
    cmd = [oda_path, str(top_folder), str(output_dir), "ACAD2018", "DXF", "1", "0", "*.DWG"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Loi convert thu muc {top_folder.name}: {result.stderr or result.stdout}")


MARGIN_MM = 3

# PyMuPdfBackend ve vector truc tiep (khong qua matplotlib) -> nhanh hon nhieu
# voi ban ve nhieu doi tuong, va tu fit/can giua trong khung trang.
RENDER_CONFIG = Configuration(
    color_policy=ColorPolicy.BLACK,
    background_policy=BackgroundPolicy.WHITE,
    circle_approximation_count=32,
    max_flattening_distance=0.1,
)
RENDER_SETTINGS = Settings(
    fit_page=True,
    min_stroke_width=0.05,
    max_stroke_width=0.15,
)


def dxf_to_pdf(dxf_path: Path, pdf_path: Path, page_w_mm: float, page_h_mm: float) -> None:
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    # Bo cac doi tuong POINT (AutoCAD hien rat nho, nhung render thanh cham tron dam).
    for point in msp.query("POINT"):
        msp.delete_entity(point)

    backend = PyMuPdfBackend()
    ctx = RenderContext(doc)
    Frontend(ctx, backend, config=RENDER_CONFIG).draw_layout(msp, finalize=True)

    page = Page(page_w_mm, page_h_mm, units=Units.mm, margins=Margins.all(MARGIN_MM))
    pdf_bytes = backend.get_pdf_bytes(page, settings=RENDER_SETTINGS)
    Path(pdf_path).write_bytes(pdf_bytes)


def _render_worker(args) -> tuple[str, str | None]:
    """Worker chay trong process rieng (de render song song nhieu loi CPU)."""
    dxf_path, pdf_path, page_w_mm, page_h_mm = args
    try:
        dxf_to_pdf(Path(dxf_path), Path(pdf_path), page_w_mm, page_h_mm)
        return pdf_path, None
    except Exception as exc:
        return pdf_path, str(exc)


def merge_folder(top_folder: Path, output_dir: Path, paper: str, landscape: bool,
                  log) -> Path:
    oda_path = find_oda_converter()
    top_folder = top_folder.resolve()
    dwg_files = collect_dwg_files(top_folder)
    if not dwg_files:
        raise RuntimeError(f"Khong co file DWG trong '{top_folder.name}'")

    page_w_mm, page_h_mm = paper_size_mm(paper, landscape)
    work_dir = Path(tempfile.mkdtemp())
    writer = PdfWriter()
    try:
        log(f"  Dang convert {len(dwg_files)} file DWG sang DXF (ODA, mot lan)...")
        t0 = time.time()
        dxf_dir = work_dir / "dxf"
        convert_folder_to_dxf(top_folder, dxf_dir, oda_path)
        log(f"  ODA xong sau {time.time() - t0:.1f}s. Dang render PDF song song...")

        # Chuan bi danh sach cong viec render (giu thu tu file).
        jobs = []
        for dwg in dwg_files:
            rel = dwg.relative_to(top_folder)
            dxf_path = dxf_dir / rel.with_suffix(".dxf")
            if not dxf_path.exists():
                log(f"  Bo qua (khong tao duoc DXF): {rel}")
                continue
            pdf_path = work_dir / f"{len(jobs):05d}_{dwg.stem}.pdf"
            jobs.append((str(dxf_path), str(pdf_path), page_w_mm, page_h_mm))

        # Render song song tren nhieu loi CPU.
        t1 = time.time()
        workers = max(1, min(len(jobs), (os.cpu_count() or 2)))
        results = {}
        with ProcessPoolExecutor(max_workers=workers) as ex:
            done = 0
            for pdf_path, err in ex.map(_render_worker, jobs):
                done += 1
                if err:
                    log(f"  Loi render {Path(pdf_path).name}: {err}")
                else:
                    results[pdf_path] = True
                if done % 10 == 0 or done == len(jobs):
                    log(f"  Da render {done}/{len(jobs)} file...")
        log(f"  Render xong sau {time.time() - t1:.1f}s. Dang gop PDF...")

        # Gop theo dung thu tu cong viec ban dau.
        for job in jobs:
            pdf_path = job[1]
            if pdf_path in results:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)

        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{top_folder.name} tong hop.pdf"
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Tuy chon in")
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        ttk.Label(self, text="Kho giay:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.paper_var = tk.StringVar(value="A3")
        ttk.Combobox(
            self, textvariable=self.paper_var, values=list(PAPER_SIZES_MM.keys()),
            state="readonly", width=12,
        ).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self, text="Huong in:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.orient_var = tk.StringVar(value="Ngang")
        frame = ttk.Frame(self)
        frame.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        ttk.Radiobutton(frame, text="Doc", variable=self.orient_var, value="Doc").pack(side="left")
        ttk.Radiobutton(frame, text="Ngang", variable=self.orient_var, value="Ngang").pack(side="left")

        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=5)
        ttk.Button(btns, text="Huy", command=self.destroy).pack(side="left", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _ok(self):
        self.result = (self.paper_var.get(), self.orient_var.get() == "Ngang")
        self.destroy()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("DWG to PDF - Gop file")
        self.root.geometry("560x420")
        self.paper = "A3"
        self.landscape = True
        self.output_dir = None

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Tuy chon in...", command=self.open_settings).pack(side="left")
        self.settings_label = ttk.Label(top, text=self._settings_text())
        self.settings_label.pack(side="left", padx=10)

        out_frame = ttk.Frame(root, padding=(10, 0))
        out_frame.pack(fill="x")
        ttk.Button(out_frame, text="Chon thu muc xuat PDF...", command=self.choose_output).pack(side="left")
        self.output_label = ttk.Label(out_frame, text="(chua chon - se luu cung cap voi thu muc nguon)")
        self.output_label.pack(side="left", padx=10)

        self.drop_zone = tk.Label(
            root,
            text="Keo tha thu muc cap 1 vao day\n(hoac bam de chon thu muc)",
            bg="#eef3fb", relief="ridge", bd=2, height=8,
        )
        self.drop_zone.pack(fill="both", expand=False, padx=10, pady=10)
        self.drop_zone.bind("<Button-1>", lambda e: self.choose_input_folders())

        if HAS_DND:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self.on_drop)
        else:
            self.drop_zone.config(text=self.drop_zone["text"] + "\n(Keo-tha can cai 'tkinterdnd2')")

        self.log_box = tk.Text(root, height=12, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _settings_text(self) -> str:
        return f"Kho giay: {self.paper}  |  Huong: {'Ngang' if self.landscape else 'Doc'}"

    def open_settings(self):
        dlg = SettingsDialog(self.root)
        if dlg.result:
            self.paper, self.landscape = dlg.result
            self.settings_label.config(text=self._settings_text())

    def choose_output(self):
        folder = filedialog.askdirectory(title="Chon thu muc xuat PDF")
        if folder:
            self.output_dir = Path(folder)
            self.output_label.config(text=str(self.output_dir))

    def choose_input_folders(self):
        folder = filedialog.askdirectory(title="Chon thu muc cap 1 chua file DWG")
        if folder:
            self.process_folders([Path(folder)])

    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        folders = [Path(p) for p in paths if Path(p).is_dir()]
        if not folders:
            messagebox.showwarning("Canh bao", "Vui long keo tha thu muc, khong phai file.")
            return
        self.process_folders(folders)

    def log(self, msg: str):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")
        self.root.update_idletasks()

    def process_folders(self, folders: list[Path]):
        threading.Thread(target=self._process_folders_thread, args=(folders,), daemon=True).start()

    def _process_folders_thread(self, folders: list[Path]):
        for folder in folders:
            out_dir = self.output_dir or folder.parent
            self.log(f"Bat dau xu ly thu muc: {folder.name}")
            try:
                result = merge_folder(folder, out_dir, self.paper, self.landscape, self.log)
                self.log(f"Hoan tat: {result}")
            except Exception as exc:
                self.log(f"LOI ({folder.name}): {exc}")
        self.log("---- Xong ----")


def main():
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
