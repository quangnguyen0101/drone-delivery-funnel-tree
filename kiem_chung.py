#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kiểm chứng Funnel Tree bằng hai cách độc lập tự động + đối chiếu tham chiếu.

Chạy:  python3 kiem_chung.py [tên.geom ...]      (mặc định: mọi input/*.geom)
       python3 kiem_chung.py --no-time            (bỏ cột thời gian)

Hai cách tự động (Chương 4):

  (a) Cận trên 1-skeleton — Dijkstra chỉ đi theo cạnh tam giác. Mọi đường đi
      như vậy cũng là đường đi hợp lệ trên mặt, nên |SP(s,v)| <= d_1(s,v).
      Điều kiện cần: nếu thuật toán trả |SP| > d_1 + 1e-9 thì chắc chắn sai.

  (c) Mặt phẳng phẳng — trên lưới phẳng, geodesic = đoạn thẳng Euclid.
      |SP(s,v)| phải khớp ||s-v|| tới sai số máy (< 1e-4).

Cách (b) (lưới tinh tiến) còn là nguyên mẫu, chưa đưa vào script này.

Đối chiếu expected/ (5/9 mesh) là kiểm tra phụ, làm tròn 4 chữ số -> sàn 1e-4.

Chỉ dùng thư viện chuẩn. Kết quả in ra stdout, dùng trực tiếp cho Chương 5.
"""

from __future__ import annotations

import argparse
import heapq
import math
import sys
import time
from pathlib import Path

from funnel_tree import Mesh, read_geom, source_for, funnel_tree, shortest_distances
from funnel_paths import funnel_tree_paths, path_length

HERE = Path(__file__).parent
EPS_UB = 1e-9          # ngưỡng "vượt cận trên" (cách a)
EPS_EUCLID = 1e-6      # ngưỡng khớp Euclid (cách c)


def _dijkstra(mesh: Mesh, s: int) -> list[float]:
    """Dijkstra trên đồ thị 1-skeleton (chỉ đi theo cạnh tam giác)."""
    adj: list[list[tuple[int, float]]] = [[] for _ in mesh.points]
    for a, b in mesh.edge_faces:
        w = mesh.dist(a, b)
        adj[a].append((b, w))
        adj[b].append((a, w))
    dist = [math.inf] * len(mesh.points)
    dist[s] = 0.0
    pq = [(0.0, s)]
    while pq:
        du, u = heapq.heappop(pq)
        if du > dist[u] + 1e-15:
            continue
        for v, w in adj[u]:
            nd = du + w
            if nd < dist[v] - 1e-15:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def _flat_grid(n: int) -> Mesh:
    pts = [(x, y, 0.0) for y in range(n) for x in range(n)]
    tris = []
    for y in range(n - 1):
        for x in range(n - 1):
            a = y * n + x
            tris += [(a, a + 1, a + n), (a + 1, a + n + 1, a + n)]
    return Mesh(pts, tris)


def check_c() -> tuple[bool, float]:
    """(c) Mặt phẳng phẳng khớp Euclid; trả (pass, sai số lớn nhất)."""
    worst = 0.0
    for n in (4, 8, 12, 16, 24):
        m = _flat_grid(n)
        for s in (0, n - 1, n * (n - 1), n * n - 1, n * n // 2):
            d = shortest_distances(m, s)
            for i in range(n * n):
                if math.isinf(d[i]):
                    return False, math.inf
                worst = max(worst, abs(d[i] - math.dist(m.points[s], m.points[i])))
    return worst <= EPS_EUCLID, worst


def _read_expected(path: Path) -> list[list[tuple[float, float, float]]]:
    out = []
    for line in path.read_text().splitlines():
        t = line.replace("[", " ").replace("]", " ").split()
        if not t:
            continue
        m = int(t[0])
        out.append([tuple(float(t[1 + 3 * i + j]) for j in range(3)) for i in range(m)])
    return out


def banner(text: str) -> None:
    print(f"\n=== {text} ===")


def main() -> None:
    ap = argparse.ArgumentParser(description="Ba cách kiểm chứng + đối chiếu expected/")
    ap.add_argument("files", nargs="*", help="tên file trong input/ (mặc định: tất cả)")
    ap.add_argument("--no-time", action="store_true", help="bỏ cột thời gian")
    a = ap.parse_args()

    files = sorted((HERE / "input").glob("*.geom"))
    if a.files:
        want = set(a.files)
        files = [f for f in files if f.name in want or str(f) in want]
    if not files:
        sys.exit("không có file .geom nào trong input/")

    banner("(a) cận trên 1-skeleton + đối chiếu expected/  (sai số tuyệt đối)")
    head = f"{'mesh':13s} {'V':>3} {'F':>3} {'E':>4} {'chi':>3} {'bnd':>3} {'s':>2} " \
           f"{'nodes':>6} {'occ':>5} {'del':>4} {'(a)vượt':>7} {'(a)max':>9} " \
           f"{'|exp|max':>9}"
    if not a.no_time:
        head += f" {'t(ms)':>8}"
    print(head)

    worst_exp = 0.0
    any_ub = False
    for f in files:
        mesh = read_geom(f)
        V, F = len(mesh.points), len(mesh.triangles)
        E = len(mesh.edge_faces)
        chi = V - E + F
        bnd = sum(1 for v in mesh.edge_faces.values() if len(v) == 1)
        s = source_for(f.name)

        t0 = time.perf_counter()
        tr = funnel_tree(mesh, s)
        d = shortest_distances(mesh, s)
        t1 = time.perf_counter()

        nodes = len(tr.nodes)
        occ = len(tr.occupied)
        dele = sum(1 for x in tr.nodes if x.deleted)

        ub = _dijkstra(mesh, s)
        over = [(d[i] - ub[i]) for i in range(V)
                if math.isfinite(d[i]) and math.isfinite(ub[i]) and d[i] > ub[i] + EPS_UB]
        if [(i) for i in range(V) if math.isfinite(d[i]) and math.isfinite(ub[i])
                and d[i] > ub[i] + EPS_UB]:
            any_ub = True
        ub_max = max([d[i] - ub[i] for i in range(V)
                      if math.isfinite(d[i]) and math.isfinite(ub[i])], default=0.0)

        exp_path = HERE / "expected" / f.name
        exp_str = "—"
        if exp_path.exists():
            pp = funnel_tree_paths(mesh, s)
            exp = _read_expected(exp_path)
            mx = max(abs(path_length(pp[v]) - path_length(exp[v]))
                     for v in range(min(len(pp), len(exp))))
            worst_exp = max(worst_exp, mx)
            exp_str = f"{mx:.2e}"

        line = (f"{f.stem:13s} {V:3d} {F:3d} {E:4d} {chi:3d} {bnd:3d} {s:2d} "
                f"{nodes:6d} {occ:5d} {dele:4d} {len(over):7d} {ub_max:9.2e} {exp_str:>9}")
        if not a.no_time:
            line += f" {(t1 - t0) * 1e3:8.2f}"
        print(line)

    print(f"\n(a) tất cả không vượt cận trên: {'ĐẠT' if not any_ub else 'KHÔNG ĐẠT'}")
    print(f"|expected| lệch lớn nhất (sàn làm tròn 1e-4): {worst_exp:.3e}")

    banner("(c) mặt phẳng phẳng — |SP(s,v)| so Euclid, lưới phẳng n×n, 5 nguồn")
    ok_c, worst_c = check_c()
    print(f"(c) sai số |SP| so Euclid lớn nhất: {worst_c:.3e} (ngưỡng {EPS_EUCLID:.0e}) "
          f"-> {'ĐẠT' if ok_c else 'KHÔNG ĐẠT'}")


if __name__ == "__main__":
    main()
