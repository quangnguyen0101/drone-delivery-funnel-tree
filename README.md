# `src/my` — Hiện thực Funnel Tree (Python)

Hiện thực lại thuật toán **Funnel Tree** (bài báo *Optimization*) trong Python thuần,
đối chiếu với bản C++ tham chiếu của anh Minh Phúc
(`../anh-minh-phuc/funnel_tree_example/`).

Hai nhánh công việc:

- **Khoảng cách** — `algorithm1.py` (+ `clip_glue.py`, `procedure2.py`): bản tối giản của
  Algorithm 1, cho độ dài đường đi ngắn nhất từ nguồn tới mọi đỉnh.
- **Đường đi** — `funnel_paths.py`: port trung thành `ft.cpp`, dựng lại **polyline** thật
  trên mặt rồi ghi ra `output/`.

## Cấu trúc

| File | Vai trò |
|------|---------|
| `algorithm1.py` | `Mesh` + `shortest_distances` (Algorithm 1, bản tối giản — chỉ khoảng cách) |
| `procedure2.py` | Thủ tục 2 (*Clip off Funnels*), nhận các cặp `(l, ∠pvz)` |
| `clip_glue.py` | `clip_with_procedure2` — nối Thủ tục 2 vào Algorithm 1 |
| `funnel_paths.py` | Port `ft.cpp`: `sub_funnel_tree` → tìm đỉnh lõm → geodesic → **trải phẳng** → polyline |
| `run.py` | Chạy Algorithm 1, so khoảng cách với `expected/`; chứa `read_geom`, `S`, `SOURCES` |
| `view_geom.py` | Xem mesh 3D + chồng lớp đường đi (Tk hoặc PNG) |
| `funnel_tree_explained.ipynb` | Notebook minh họa |
| `input/` | 7 mesh `.geom` (+ `city.glb`) |
| `expected/` | Output C++ tham chiếu (cho `J17, L, cliff, demo_mesh, star`) |
| `output/` | Output của Python (đủ 7 mesh) |
| `view/` | Ảnh PNG do `view_geom.py` xuất |

## Định dạng `.geom`

**Input** (`input/*.geom`, đọc bởi `run.read_geom`):

```
v f E
x y z            (v dòng)
3 i j k          (f dòng, tam giác)
```

**Đường đi / output** (`expected/*.geom`, `output/*.geom`, đọc bởi `view_geom.read_paths`):
mỗi dòng một đỉnh, `m x y z x y z ...` = đường gấp khúc từ nguồn tới đỉnh đó
(đỉnh nguồn: `m=2`, hai điểm trùng). Tọa độ làm tròn 4 chữ số.

## Đỉnh nguồn `s` theo mesh

`expected/` lấy `s` đúng như bài báo; `run.py:SOURCES` giữ bảng này để các script tự chọn:

| mesh | `s` | nguồn |
|------|-----|-------|
| `cube.geom` (Hình 7) | 4 | bài báo |
| `icosahedron.geom` (Hình 4) | 0 | bài báo |
| `star.geom` | 0 | khớp `expected/` |
| còn lại (`J17, L, cliff, demo_mesh`) | 1 | `ft_main.cpp` |

## Cách chạy

Chỉ `view_geom.py` cần thư viện ngoài (`matplotlib`, tùy chọn `tkinter`); các script
còn lại thuần Python chuẩn, chạy bằng `python3` hệ thống:

```sh
cd 3.2-drone-delivery/src/my

python3 run.py                     # Algorithm 1: khoảng cách vs expected/
python3 funnel_paths.py            # dựng lại đường đi -> output/ (nguồn theo SOURCES)
python3 funnel_paths.py --check    # so đường đi với expected/ (lệch max)
python3 funnel_paths.py -s 4 cube.geom
python3 view_geom.py               # xem tất cả (Tk) / PNG nếu thiếu Tk
```

`view_geom.py` chồng lớp đường đi — **đỏ liền** = `output/` của ta, **xanh lá đứt** =
`expected/` (C++). Chọn lớp bằng `--paths`:

```sh
python3 view_geom.py --paths output     # chỉ của ta
python3 view_geom.py --paths expected   # chỉ tham chiếu
python3 view_geom.py --paths both       # cả hai (mặc định)
python3 view_geom.py --paths none       # chỉ mesh
python3 view_geom.py --png --no-open cliff.geom    # xuất view/cliff.png
```

## Kiểm chứng

- `funnel_paths.py --check`: **lệch max = 0** so với `expected/` cho `J17, L, cliff,
  demo_mesh` (`s=1`) và `star` (`s=0`). `cube`/`icosahedron` không có `expected/`
  (chỉ có hình vẽ trong bài báo).
- `run.py`: khoảng cách Algorithm 1 khớp `J17` (lệch ~1e-5, do C++ làm tròn 4 chữ số);
  các mesh có đỉnh lõm (`L, cliff, star, demo_mesh`) lệch nhiều hơn — đúng như dự kiến
  với bản tối giản chưa xử lý đầy đủ Thủ tục 2.
