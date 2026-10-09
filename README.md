# Funnel Tree — Hiện thực Python

Hiện thực lại thuật toán **Funnel Tree** trong Python thuần,
dựa trên thuật toán Funnel Tree.

Hai nhánh công việc:

- **Khoảng cách** — `funnel_tree.py` (+ `funnel_clip_glue.py`, `funnel_clip.py`): hiện thực Thuật toán 1 + Thủ tục 2 theo bài báo,
  cho độ dài đường đi ngắn nhất từ nguồn tới mọi đỉnh.
- **Đường đi** — `funnel_paths.py`: dựng lại polyline đường đi trên mặt đa diện theo thuật toán Funnel Tree.

## Cấu trúc

| File | Vai trò |
|------|---------|
| `funnel_tree.py` | `Mesh` + `shortest_distances` (Thuật toán 1 + Thủ tục 2 — tính khoảng cách ngắn nhất), đọc `.geom` (`read_geom`), bảng nguồn `SOURCES` |
| `funnel_paths.py` | Hiện thực truy hồi polyline theo thuật toán Funnel Tree (theo bài báo) |
| `funnel_clip.py` | Thủ tục 2 (*Clip off Funnels*) |
| `funnel_clip_glue.py` | `clip_with_procedure2` — nối Thủ tục 2 vào Algorithm 1 |
| `view_geom.py` | Xem mesh 3D + chồng lớp đường đi (Tk hoặc PNG) |
| `input/` | 9 mesh `.geom` (+ `city.glb`) |
| `expected/` | Output tham chiếu (cho `J17, L, cliff, demo_mesh, star`) |
| `output/` | Output của Python (mọi mesh trong `input/`) |
| `view/` | Ảnh PNG do `view_geom.py` xuất |

## Định dạng `.geom`

**Input** (`input/*.geom`, đọc bởi `funnel_tree.read_geom`):

```
v f E
x y z            (v dòng)
3 i j k          (f dòng, tam giác)
```

**Đường đi / output** (`expected/*.geom`, `output/*.geom`, đọc bởi `view_geom.read_paths`):
mỗi dòng một đỉnh, `m x y z x y z ...` = đường gấp khúc từ nguồn tới đỉnh đó
(đỉnh nguồn: `m=2`, hai điểm trùng). Tọa độ làm tròn 4 chữ số.

## Đỉnh nguồn `s` theo mesh

`expected/` lấy `s` đúng như bài báo; `funnel_tree.py:SOURCES` giữ bảng này để các script tự chọn:

| mesh | `s` | nguồn |
|------|-----|-------|
| `cube.geom` (Hình 7) | 4 | bài báo |
| `icosahedron.geom` (Hình 4) | 0 | bài báo |
| `star.geom` | 0 | khớp `expected/` |
| `dome.geom` (bề mặt mở) | 17 | mở rộng — biên |
| `terrain.geom` (địa hình hở + lõm) | 24 | mở rộng — giữa mesh |
| còn lại (`J17, L, cliff, demo_mesh`) | 1 | `ft_main.cpp` |

## Cách chạy

Chỉ `view_geom.py` cần thư viện ngoài (`matplotlib`, tùy chọn `tkinter`); các script
còn lại thuần Python chuẩn, chạy bằng `python3` hệ thống:

```sh
python3 funnel_paths.py            # dựng lại đường đi -> output/ (nguồn theo SOURCES)
python3 funnel_paths.py --check    # so đường đi với expected/ (lệch max)
python3 funnel_paths.py -s 4 cube.geom
python3 view_geom.py               # xem tất cả (Tk) / PNG nếu thiếu Tk
```

`view_geom.py` chồng lớp đường đi — **đỏ liền** = `output/` của ta, **xanh lá đứt** =
`expected/` là output tham chiếu để so sánh. Chọn lớp bằng `--paths`:

```sh
python3 view_geom.py --paths output     # chỉ của ta
python3 view_geom.py --paths expected   # chỉ tham chiếu
python3 view_geom.py --paths both       # cả hai (mặc định)
python3 view_geom.py --paths none       # chỉ mesh
python3 view_geom.py --png --no-open cliff.geom    # xuất view/cliff_both.png
```

Ảnh PNG xuất vào `view/<tên>_<option>.png` (`<option>` = both | expected | output | none).

## Kiểm chứng

- `funnel_paths.py --check`: **lệch max = 0** so với `expected/` cho `J17, L, cliff,
  demo_mesh` (`s=1`) và `star` (`s=0`). `cube`/`icosahedron` không có `expected/`
  (chỉ có hình vẽ trong bài báo (hiện thực tham khảo)).
- Bề mặt mở: `dome` (lồi, biên), `terrain` (địa hình có lõm) — mọi đỉnh tới được từ `s`;
  `terrain` nguồn giữa mesh khớp distance trong lỗi làm tròn.
- `run.py` đã bỏ (gộp toàn bộ vào `funnel_tree.py` / `funnel_paths.py`).
- `funnel_tree.py` `__main__`: tự-kiểm tra bề mặt mở trải khớp Euclid → `PASS`.
