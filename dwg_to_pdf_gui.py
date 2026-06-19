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
    - pip install tkinterdnd2 pypdf ezdxf matplotlib
"""
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

import ezdxf
from ezdxf import bbox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, ColorPolicy, BackgroundPolicy
from pypdf import PdfReader, PdfWriter

PAPER_SIZES_MM = {
    "A0": (841, 1189),
    "A1": (594, 841),
    "A2": (420, 594),
    "A3": (297, 420),
    "A4": (210, 297),
    "Letter": (215.9, 279.4),
}
MM_TO_IN = 1 / 25.4


def paper_size_inches(name: str, landscape: bool) -> tuple[float, float]:
    w_mm, h_mm = PAPER_SIZES_MM[name]
    w_in, h_in = w_mm * MM_TO_IN, h_mm * MM_TO_IN
    if landscape:
        w_in, h_in = max(w_in, h_in), min(w_in, h_in)
    else:
        w_in, h_in = min(w_in, h_in), max(w_in, h_in)
    return w_in, h_in


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
    return sorted(p for p in root_folder.rglob("*.dwg") if p.is_file()) + \
        sorted(p for p in root_folder.rglob("*.DWG") if p.is_file())


def convert_dwg_to_dxf(dwg_path: Path, output_dir: Path, oda_path: str) -> Path:
    src_dir = Path(tempfile.mkdtemp())
    shutil.copy(dwg_path, src_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [oda_path, str(src_dir), str(output_dir), "ACAD2018", "DXF", "0", "1", "*.DWG"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    shutil.rmtree(src_dir, ignore_errors=True)
    if result.returncode != 0:
        raise RuntimeError(f"Loi convert {dwg_path.name}: {result.stderr or result.stdout}")
    dxf_path = output_dir / (dwg_path.stem + ".dxf")
    if not dxf_path.exists():
        raise RuntimeError(f"Khong tao duoc DXF cho {dwg_path.name}")
    return dxf_path


def dxf_to_pdf(dxf_path: Path, pdf_path: Path, page_w_in: float, page_h_in: float) -> None:
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    fig = plt.figure(figsize=(page_w_in, page_h_in))
    # Axes fills the entire page so the drawing fits to the paper edges.
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.axis("off")

    # In trang den: ve tat ca doi tuong mau den tren nen trang.
    cfg = Configuration(
        color_policy=ColorPolicy.BLACK,
        background_policy=BackgroundPolicy.WHITE,
    )
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=cfg).draw_layout(msp, finalize=True)

    # Fit ban ve kin kho giay theo gioi han thuc te cua ban ve.
    try:
        extents = bbox.extents(msp)
        if extents.has_data:
            min_x, min_y = extents.extmin.x, extents.extmin.y
            max_x, max_y = extents.extmax.x, extents.extmax.y
            ax.set_xlim(min_x, max_x)
            ax.set_ylim(min_y, max_y)
    except Exception:
        pass
    ax.margins(0)

    fig.savefig(str(pdf_path), facecolor="white")
    plt.close(fig)


def merge_folder(top_folder: Path, output_dir: Path, paper: str, landscape: bool,
                  log) -> Path:
    oda_path = find_oda_converter()
    dwg_files = collect_dwg_files(top_folder)
    if not dwg_files:
        raise RuntimeError(f"Khong co file DWG trong '{top_folder.name}'")

    page_w_in, page_h_in = paper_size_inches(paper, landscape)
    work_dir = Path(tempfile.mkdtemp())
    writer = PdfWriter()
    try:
        for dwg in dwg_files:
            log(f"  Dang convert: {dwg.relative_to(top_folder)}")
            dxf_path = convert_dwg_to_dxf(dwg, work_dir, oda_path)
            pdf_path = work_dir / (dwg.stem + ".pdf")
            dxf_to_pdf(dxf_path, pdf_path, page_w_in, page_h_in)
            reader = PdfReader(str(pdf_path))
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
