#!/usr/bin/env python3
"""Convert DWG files to PDF using the ODA File Converter CLI.

Requires ODA File Converter installed: https://www.opendesign.com/guestfiles/oda_file_converter
On Linux/macOS the binary is typically named "ODAFileConverter".
On Windows it is "ODAFileConverter.exe".

Usage:
    python dwg_to_pdf.py <input_dir_or_file> <output_dir> [--oda-path PATH]
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_oda_converter(custom_path: str | None) -> str:
    if custom_path:
        return custom_path
    for name in ("ODAFileConverter", "ODAFileConverter.exe"):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError(
        "ODA File Converter not found. Install it from "
        "https://www.opendesign.com/guestfiles/oda_file_converter "
        "or pass its path with --oda-path."
    )


def convert_dwg_to_pdf(input_path: Path, output_dir: Path, oda_path: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        if input_path.suffix.lower() != ".dwg":
            raise ValueError(f"Not a DWG file: {input_path}")
        src_dir = tempfile.mkdtemp()
        shutil.copy(input_path, src_dir)
        input_dir = src_dir
    else:
        input_dir = str(input_path)

    # Args: InputFolder OutputFolder OutputVersion OutputType Recurse Audit [Filter]
    cmd = [
        oda_path,
        input_dir,
        str(output_dir),
        "ACAD2018",
        "PDF",
        "0",  # recurse
        "1",  # audit
        "*.DWG",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ODA File Converter failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert DWG file(s) to PDF.")
    parser.add_argument("input", help="DWG file or folder containing DWG files")
    parser.add_argument("output", help="Output folder for generated PDFs")
    parser.add_argument("--oda-path", help="Path to ODAFileConverter executable")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        print(f"Error: input path does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        oda_path = find_oda_converter(args.oda_path)
        convert_dwg_to_pdf(input_path, output_dir, oda_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Done. PDFs written to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
