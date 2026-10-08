#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chạy Algorithm 1 + Procedure 2 trên các file .geom, so với output tham chiếu.

Nguồn mặc định: s = 1 (0-based), input/<file>.geom -> output/<file>.geom
Output tham chiếu: mien dong, moi dong <so diem> x y z x y z ...
Ta tinh do dai duong di gon tu output do va so sanh voi dist() cua thuat toan 1.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

from algorithm1 import Mesh, shortest_distances
from clip_glue import clip_with_procedure2

S = 1  # nguon, giong 
# Nguồn khác mặc định, theo bài báo / expected/: cube (Hình 7) s=4, icosahedron
# (Hình 4) s=0; expected/star.geom cũng dựng bằng s=0.
SOURCES = {"cube.geom": 4, "icosahedron.geom": 0, "star.geom": 0}


def source_for(name: str, default: int = S) -> int:
    return SOURCES.get(name, default)


def read_geom(path: Path) -> Mesh:
    tok = path.read_text().split()
    v, f = int(tok[0]), int(tok[1])
    pts, tris, k = [], [], 3
    for i in range(v):
        pts.append((float(tok[k]), float(tok[k + 1]), float(tok[k + 2])))
        k += 3
    for _ in range(f):
        assert int(tok[k]) == 3, "chi ho tro tam giac"
        tris.append((int(tok[k + 1]), int(tok[k + 2]), int(tok[k + 3])))
        k += 4
    return Mesh(pts, tris)


def cpp_path_lengths(path: Path, nvertex: int) -> list[float]:
    """Do dai duong di tu output tham chiếu. Dong thu i ung dinh i ( ghi theo thu tu).

    Output tham chiếu: <m> [x y z] [x y z] ... , lam tron 4 chu so.
    """
    lines = [l for l in path.read_text().split("\n") if l.strip()]
    assert len(lines) == nvertex, f"{path.name}: {len(lines)} dong != {nvertex} dinh"
    out = []
    for line in lines:
        t = line.replace("[", " ").replace("]", " ").split()
        m = int(t[0])
        assert 3 * m + 1 == len(t), f"dong khong dung dinh dang: {line[:40]}"
        pts = [(float(t[1 + 3 * i]), float(t[2 + 3 * i]), float(t[3 + 3 * i]))
               for i in range(m)]
        out.append(sum(math.dist(pts[i], pts[i + 1]) for i in range(m - 1)))
    return out


def edge_dijkstra(mesh: Mesh, s: int) -> list[float]:
    """Cận trên: đường đi ngắn nhất trên 1-skeleton (chỉ đi cạnh tam giác).

    Không cần file C++: 1-skeleton la subset cua mat, nen do dai nay >= do dai
    tren mat. Algorithm 1 ra so lon hon cận trên = sai chắc chắn.
    """
    import heapq

    INF = math.inf
    d = [INF] * len(mesh.points)
    d[s] = 0.0
    pq = [(0.0, s)]
    while pq:
        du, u = heapq.heappop(pq)
        if du > d[u]:
            continue
        for (a, b) in mesh.edge_faces:
            if a == u:
                v = b
            elif b == u:
                v = a
            else:
                continue
            nd = du + mesh.dist(u, v)
            if nd < d[v]:
                d[v] = nd
                heapq.heappush(pq, (nd, v))
    return d


def main() -> None:
    here = Path(__file__).parent
    files = sorted((here / "input").glob("*.geom"))
    if len(sys.argv) > 1:
        files = [f for f in files if f.name in sys.argv[1:]]
    worst_overall = 0.0
    for f in files:
        mesh = read_geom(f)
        s = source_for(f.name)
        t0 = time.perf_counter()
        try:
            dist = shortest_distances(mesh, s, clip_with_procedure2)
        except Exception as e:
            print(f"{f.name:18s} V0 ngoai le: {type(e).__name__}: {e}")
            continue
        dt = time.perf_counter() - t0
        ub = edge_dijkstra(mesh, s)

        # kiem tra doc lap: dist > cahn tren -> sai chắc chắn
        over = [(d - ub[v], v) for v, d in enumerate(dist)
                if not math.isinf(d) and d > ub[v] + 1e-9]
        inf_v = [v for v, d in enumerate(dist) if math.isinf(d)]
        exp_path = here / "expected" / f.name
        if not exp_path.exists():
            print(f"{f.name:18s} v={len(mesh.points):3d} f={len(mesh.triangles):3d} "
                  f"{dt * 1000:7.1f}ms  vuotCanTren={len(over):2d}  "
                  f"khongToi={len(inf_v):2d}  (khong co expected/)")
            continue
        exp = cpp_path_lengths(exp_path, len(mesh.points))
        # output tham chiếu lam tron 4 chu so -> sai so do do chinh no, khong phai thuat toan
        errs = sorted(((abs(dist[v] - L), v) for v, L in enumerate(exp)),
                      reverse=True)
        top = errs[0] if errs else (0.0, -1)
        worst_overall = max(worst_overall, top[0])
        print(f"{f.name:18s} v={len(mesh.points):3d} f={len(mesh.triangles):3d} "
              f"{dt * 1000:7.1f}ms  "
              f"vuotCanTren={len(over):2d}  khongToi={len(inf_v):2d}  "
              f"|C++ lech={sum(e > 1e-3 for e, _ in errs):2d} "
              f"max={top[0]:.4g}")
        for e, v in sorted(over, reverse=True)[:3]:
            print(f"    vuot {e:.4f} tai dinh {v} "
                  f"({mesh.points[v][0]:.2f},{mesh.points[v][1]:.2f},"
                  f"{mesh.points[v][2]:.2f})")
    print(f"\nsai lon nhat so voi output tham chiếu: {worst_overall:.6g}")


if __name__ == "__main__":
    main()
