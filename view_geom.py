#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hiển thị file .geom (đầu vào của Algorithm 1).

Có Tk → mở cửa sổ 3D, xoay/thu phóng bằng chuột.
Không Tk (venv uv thiếu _tkinter) → xuất ảnh PNG view/*.png rồi xdg-open.

    python view_geom.py                 # tất cả input/*.geom
    python view_geom.py cliff.geom      # chỉ 1 file
    python view_geom.py --wire          # chỉ khung dây, không tô mặt
    python view_geom.py --png           # ép xuất PNG kể cả khi có Tk
    python view_geom.py cliff.geom -o a.png
    python view_geom.py --paths expected   # chỉ lớp của expected
    python view_geom.py --paths output     # chỉ lớp của output
    python view_geom.py --paths none       # không vẽ đường đi

Mặc định chồng HAI lớp đường đi ngắn nhất (định dạng output C++:
mỗi dòng `m x y z x y z ...`):
    - đỏ liền  : output/ (do ta dựng bằng funnel_paths.py)
    - xanh lá đứt : expected/ (tham chiếu, output C++)
Chọn lớp bằng --paths {both,output,expected,none}.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import matplotlib

try:
    import tkinter  # noqa: F401
    matplotlib.use("TkAgg")
    INTERACTIVE = True
except Exception:
    matplotlib.use("Agg")
    INTERACTIVE = False

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from algorithm1 import Mesh  # noqa: E402
from run import S, SOURCES, read_geom, source_for  # noqa: E402


def read_paths(path: Path) -> list[list[tuple[float, float, float]]]:
    """Đọc file đường đi (định dạng output C++ / expected/*.geom).

    Mỗi dòng: `m x y z x y z ...` = đường gấp khúc từ s tới đỉnh tương ứng.
    """
    out = []
    for line in path.read_text().splitlines():
        t = line.replace("[", " ").replace("]", " ").split()
        if not t:
            continue
        m = int(t[0])
        assert 3 * m + 1 == len(t), f"{path.name}: dòng sai định dạng: {line[:40]}"
        out.append([tuple(float(x) for x in t[1 + 3 * i:4 + 3 * i]) for i in range(m)])
    return out


def draw_paths(ax, paths: list[list[tuple[float, float, float]]],
               color: str | None = None, style: str = "-",
               lw: float = 1.8) -> int:
    cmap = plt.get_cmap("turbo")
    n = max(len(paths) - 1, 1)
    drawn = 0
    for i, pts in enumerate(paths):
        if len(pts) < 2:
            continue
        xs, ys, zs = zip(*pts)
        if max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) < 1e-9:
            continue                      # đường dài 0 (chính đỉnh nguồn)
        ax.plot(xs, ys, zs, color=color or cmap(i / n), linestyle=style,
                linewidth=lw, zorder=6, solid_capstyle="round")
        drawn += 1
    return drawn


def render(mesh: Mesh, title: str, wire: bool = False, source: int = S,
           layers: list[dict] | None = None) -> plt.Figure:
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    tris = [list(mesh.points[i] for i in t) for t in mesh.triangles]
    if not wire:
        ax.add_collection3d(Poly3DCollection(
            tris, facecolor="#7fb3ff", edgecolor="#33415e",
            linewidths=0.6, alpha=0.45))
    ax.add_collection3d(Poly3DCollection(
        tris, facecolor="none", edgecolor="#1f2a44", linewidths=0.7))

    xs, ys, zs = zip(*mesh.points)
    ax.scatter(xs, ys, zs, s=14, depthshade=False, color="#0f172a")
    if 0 <= source < len(mesh.points):
        p = mesh.points[source]
        ax.scatter([p[0]], [p[1]], [p[2]], s=90, depthshade=False,
                   marker="*", color="#dc2626", zorder=5)
    for i, p in enumerate(mesh.points):
        ax.text(p[0], p[1], p[2], f" {i}", fontsize=7, color="#b91c1c")

    handles = []
    for ly in (layers or []):
        c = draw_paths(ax, ly["paths"], color=ly.get("color"),
                       style=ly.get("style", "-"))
        if c:
            handles.append(plt.Line2D([], [], color=ly["color"], linestyle=ly.get("style", "-"),
                                      linewidth=2, label=f"{ly['label']} ({c})"))

    lo = [min(c) for c in zip(*mesh.points)]
    hi = [max(c) for c in zip(*mesh.points)]
    ctr = [(a + b) / 2 for a, b in zip(lo, hi)]
    r = max((b - a) / 2 for a, b in zip(lo, hi)) or 1.0
    ax.set_xlim(ctr[0] - r, ctr[0] + r)
    ax.set_ylim(ctr[1] - r, ctr[1] + r)
    ax.set_zlim(ctr[2] - r, ctr[2] + r)
    ax.set_box_aspect((1, 1, 1))

    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.view_init(elev=22, azim=-60)
    ax.set_title(f"{title}   V={len(mesh.points)} F={len(mesh.triangles)}")
    if not wire:
        patch = [Patch(facecolor="#7fb3ff", edgecolor="#33415e", alpha=0.6,
                       label="mặt tam giác"),
                 plt.Line2D([], [], marker="*", color="#dc2626", ls="",
                            label=f"đỉnh nguồn s={source}")]
        ax.legend(handles=patch + handles, loc="upper left", fontsize=8)
    fig.tight_layout()
    return fig


def main() -> None:
    here = Path(__file__).parent
    ap = argparse.ArgumentParser(description="Vẽ file .geom (cửa sổ Tk hoặc PNG)")
    ap.add_argument("files", nargs="*", help="tên file trong input/ (mặc định: tất cả)")
    ap.add_argument("-o", "--out", help="đường dẫn PNG (chỉ dùng khi có đúng 1 file)")
    ap.add_argument("--png", action="store_true", help="ép xuất PNG dù có Tk")
    ap.add_argument("--no-open", action="store_true", help="không mở ảnh sau khi xuất PNG")
    ap.add_argument("--wire", action="store_true", help="chỉ vẽ khung dây")
    ap.add_argument("-s", "--source", type=int, default=None,
                    help=f"đỉnh nguồn (mặc định theo input: {', '.join(f'{k}={v}' for k, v in sorted(SOURCES.items()))})")
    ap.add_argument("--paths", choices=["both", "output", "expected", "none"],
                    default="both",
                    help="lớp đường đi hiển thị: both (mặc định) | output | expected | none")
    a = ap.parse_args()

    to_png = a.png or bool(a.out) or not INTERACTIVE

    files = sorted((here / "input").glob("*.geom"))
    if a.files:
        want = set(a.files)
        files = [f for f in files if f.name in want or str(f) in want]
        miss = want - {f.name for f in files}
        if miss:
            sys.exit(f"không tìm thấy: {', '.join(sorted(miss))}")
    if not files:
        sys.exit("không có file .geom nào trong input/")

    outdir = here / "view"
    outdir.mkdir(exist_ok=True)
    for f in files:
        mesh = read_geom(f)
        layers = []
        if a.paths != "none":
            if a.paths in ("both", "output"):
                pf = here / "output" / f.name
                if pf.exists():
                    layers.append({"paths": read_paths(pf), "color": "#dc2626",
                                   "style": "-", "label": "output (thuật toán)"})
            if a.paths in ("both", "expected"):
                pf = here / "expected" / f.name
                if pf.exists():
                    layers.append({"paths": read_paths(pf), "color": "#16a34a",
                                   "style": "--", "label": "expected (C++)"})
        fig = render(mesh, f.name, wire=a.wire,
                     source=(a.source if a.source is not None else source_for(f.name)),
                     layers=layers)
        print(f"{f.name:18s} V={len(mesh.points):3d} F={len(mesh.triangles):3d}", end="")
        for ly in layers:
            print(f" {ly['label'].split()[0]}={len(ly['paths']):3d}", end="")
        if not to_png:
            plt.show()          # chặn tới khi đóng cửa sổ, rồi mới sang file sau
            plt.close(fig)
            print("  (cửa sổ đã đóng)")
            continue
        out = Path(a.out) if a.out else outdir / f"{f.stem}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=140, bbox_inches="tight")
        plt.close(fig)
        print(f" -> {out}")
        if not a.no_open and not a.out:
            subprocess.run(["xdg-open", str(out)], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
