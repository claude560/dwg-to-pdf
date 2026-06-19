"""Cau truc du lieu mo ta 1 doan cot/keo va khung 2D."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Segment:
    """Mot doan cot hoac keo (thep to hop)."""

    name: str               # ten doan, vd "C1", "R2" - lay tu text trong DXF
    kind: str               # "column" | "rafter"
    length: float           # chieu dai doan (mm), lay tu DIMENSION trong DXF
    section: str = ""       # tiet dien thep to hop, lay tu file attribute
    start: tuple[float, float] | None = None  # diem dau (x, y) sau khi dung hinh
    end: tuple[float, float] | None = None    # diem cuoi (x, y) sau khi dung hinh


@dataclass
class Frame:
    """Khung 2D gom nhieu doan cot/keo noi tiep theo dung 1 duong polyline."""

    segments: list[Segment] = field(default_factory=list)
    origin: tuple[float, float] = (0.0, 0.0)  # diem trai-duoi nguoi dung chon

    def total_length(self) -> float:
        return sum(s.length for s in self.segments)

    def points(self) -> list[tuple[float, float]]:
        """Danh sach toa do cac diem noi tiep (origin -> ... -> diem cuoi)."""
        pts = [self.origin]
        for s in self.segments:
            if s.end is not None:
                pts.append(s.end)
        return pts
