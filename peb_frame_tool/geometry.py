"""Dung hinh hoc khung 2D (cot + keo, ke ca nhieu nhip / cot giua) tu danh sach doan.

Khung duoc mo ta nhu 1 duong polyline noi tiep cac doan, bat dau tu diem goc
(trai-duoi) nguoi dung chon. Moi doan can biet truoc GOC nghieng (so voi
phuong ngang, do) - vi DIMENSION trong DXF chi cho chieu dai, khong cho huong.

Vi du khung 2 nhip, 1 cot giua, mai 2 doc deu:
    cot bien trai   : 90 do  (di len)
    keo trai-1       : +alpha do (di len, doc len ma)
    cot giua (neu co): 90 do hoac -90 do tuy dinh nghia
    keo trai-2 (toi dinh) : +alpha do
    keo phai-1 (tu dinh xuong) : -alpha do
    cot giua phai    : -90 do (di xuong)
    keo phai-2       : -alpha do
    cot bien phai    : -90 do (di xuong)

Goc nghieng alpha co the tinh tu ty le mai (vd 10%) hoac doc tiep tu 2 dimension
(chieu dai nghieng + chieu cao chenh) trong DXF.
"""
from __future__ import annotations

import math

from .models import Frame, Segment


def slope_angle_from_rise_run(rise: float, run: float) -> float:
    """Goc nghieng (do) tu do chenh cao (rise) va khoang chay ngang (run)."""
    return math.degrees(math.atan2(rise, run))


def build_frame(
    segment_specs: list[tuple[Segment, float]],
    origin: tuple[float, float] = (0.0, 0.0),
) -> Frame:
    """segment_specs: list (Segment, goc_do) - goc do tinh tu phuong ngang,
    duong khoa nguoc chieu kim dong ho (90 = thang dung di len).

    Tra ve Frame da co toa do start/end cho tung doan.
    """
    frame = Frame(origin=origin)
    cur = origin
    for seg, angle_deg in segment_specs:
        angle = math.radians(angle_deg)
        nxt = (
            cur[0] + seg.length * math.cos(angle),
            cur[1] + seg.length * math.sin(angle),
        )
        seg.start = cur
        seg.end = nxt
        frame.segments.append(seg)
        cur = nxt
    return frame


def gable_frame_angles(num_bays: int, has_inner_columns: bool = True) -> list[str]:
    """Sinh chuoi loai goc cho 1 khung mai 2 doc, nhieu nhip, doi xung:
    tra ve list cac token: "up" (cot di len), "down" (cot di xuong),
    "rise" (keo di len toi dinh), "fall" (keo di xuong tu dinh).

    Day chi la khung dinh huong tham khao - ghep voi danh sach Segment thuc te
    (theo dung thu tu doc duoc tu DXF) de tao segment_specs cho build_frame().
    """
    tokens = ["up"]  # cot bien trai
    for bay in range(num_bays):
        tokens.append("rise")
        tokens.append("fall")
        if has_inner_columns and bay < num_bays - 1:
            tokens.append("down")
            tokens.append("up")
    tokens.append("down")  # cot bien phai
    return tokens
