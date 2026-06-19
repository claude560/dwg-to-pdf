# PEB Frame Tool (dang xay dung)

Muc tieu: tu dong ve mat cat khung nha tien che (cot + keo thep to hop) vao
Tekla Structures, dau vao la file DXF mat cat 2D + file attribute tiet dien.

## Trang thai hien tai

Da co (chay duoc tren may khong can Tekla, chi can `pip install ezdxf openpyxl`):

- `dxf_reader.py` - doc DIMENSION + TEXT/MTEXT tu file DXF, ghep ten doan voi
  kich thuoc gan nhat. Chay thu:
  ```
  python -m peb_frame_tool.dxf_reader duong/dan/file.dxf
  ```
  In ra toan bo text va dimension tim duoc kem toa do - dung de kiem tra xem
  file DXF thuc te cua ban co dung quy uoc (DIMENSION + TEXT canh ben) khong,
  truoc khi viet logic ghep noi tu dong chinh xac hon.

- `attribute_loader.py` - doc file attribute (.csv/.txt/.xlsx) dang 2 cot
  "ten doan, tiet dien" thanh dict tra cuu.

- `geometry.py` - dung toa do (x, y) cho tung doan cot/keo tu danh sach
  (Segment, goc_do), bat dau tu 1 diem goc. Ho tro khung nhieu nhip/cot giua
  thong qua chuoi goc do tuy chinh (xem `gable_frame_angles`).

- `models.py` - dataclass `Segment`, `Frame`.

## Con thieu / can lam tiep

1. **Chay thu `dxf_reader.inspect()` tren 1 file DXF that** cua ban (xuat tu
   Tekla hoac CAD) de xac nhan dimension/text co dung vi tri nhu gia dinh.
   Neu khong dung quy uoc (vd ten doan nam trong layer rieng, hoac dung
   ATTRIB/BLOCK thay vi TEXT), can chinh lai `extract_texts()`.
2. **Xac dinh ten Custom Component "PEB" trong Tekla** (xem trong
   Applications & Components, hover de xem ten/so component), va cac
   tham so input cua no (kieu thep to hop, be rong canh, chieu day bung...).
3. Viet `tekla_writer.py` dung `pythonnet`:
   - `clr.AddReference("Tekla.Structures.Model")`
   - tao `Component`, gan input points + attributes, `Insert()`.
   Phan nay phai chay tren may co Tekla cai san, se hoan thien sau khi co
   thong tin tu buoc 2.
4. Viet script chinh (`main.py`) noi cac buoc: doc DXF -> doc attribute ->
   dung hinh hoc -> ve vao Tekla.
