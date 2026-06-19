"""Doc file DXF mat cat khung 2D: lay kich thuoc (DIMENSION) va ten doan (TEXT/MTEXT).

Dung de kham pha 1 file DXF thuc te truoc, vi cach dat ten/kich thuoc co the
khac nhau giua cac du an - chua co quy tac co dinh de tu dong ghep noi.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import ezdxf


@dataclass
class DimRecord:
    measurement: float          # gia tri kich thuoc (theo don vi ve, thuong la mm)
    position: tuple[float, float]  # vi tri text cua dimension (de doi chieu)
    dimtype: str                 # loai dimension (linear, aligned, angular...)


@dataclass
class TextRecord:
    content: str
    position: tuple[float, float]


def load_doc(dxf_path: str):
    return ezdxf.readfile(dxf_path)


def extract_dimensions(doc) -> list[DimRecord]:
    msp = doc.modelspace()
    records = []
    for dim in msp.query("DIMENSION"):
        try:
            measurement = dim.get_measurement()
        except Exception:
            measurement = None
        pos = dim.dxf.text_midpoint if dim.dxf.hasattr("text_midpoint") else dim.dxf.defpoint
        records.append(
            DimRecord(
                measurement=float(measurement) if measurement else 0.0,
                position=(pos.x, pos.y),
                dimtype=dim.dimtype_str if hasattr(dim, "dimtype_str") else str(dim.dxf.dimtype),
            )
        )
    return records


def extract_texts(doc) -> list[TextRecord]:
    msp = doc.modelspace()
    records = []
    for e in msp.query("TEXT MTEXT"):
        content = e.dxf.text if e.dxftype() == "TEXT" else e.text
        pos = e.dxf.insert
        records.append(TextRecord(content=content.strip(), position=(pos.x, pos.y)))
    return records


def _dist(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def match_labels_to_dimensions(
    dims: list[DimRecord], texts: list[TextRecord], max_dist: float = 500.0
) -> list[tuple[DimRecord, TextRecord | None]]:
    """Voi moi dimension, tim text gan nhat (vd ten doan "C1") trong pham vi max_dist.

    max_dist tinh theo don vi ve (thuong mm) - chinh lai cho phu hop voi ban ve thuc te.
    """
    pairs = []
    for d in dims:
        best, best_dist = None, max_dist
        for t in texts:
            dist = _dist(d.position, t.position)
            if dist < best_dist:
                best, best_dist = t, dist
        pairs.append((d, best))
    return pairs


def inspect(dxf_path: str) -> None:
    """In ra toan bo DIMENSION va TEXT tim duoc - dung de kham pha 1 file DXF moi."""
    doc = load_doc(dxf_path)
    dims = extract_dimensions(doc)
    texts = extract_texts(doc)
    print(f"Tim thay {len(dims)} DIMENSION, {len(texts)} TEXT/MTEXT trong '{dxf_path}'\n")

    print("--- TEXT/MTEXT ---")
    for t in texts:
        print(f"  '{t.content}'  @ ({t.position[0]:.1f}, {t.position[1]:.1f})")

    print("\n--- DIMENSION (ghep voi text gan nhat) ---")
    for d, t in match_labels_to_dimensions(dims, texts):
        label = t.content if t else "(khong tim duoc text gan)"
        print(f"  {d.measurement:.1f}  [{d.dimtype}]  @ ({d.position[0]:.1f}, {d.position[1]:.1f})  -> '{label}'")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Dung: python dxf_reader.py <file.dxf>")
        sys.exit(1)
    inspect(sys.argv[1])
