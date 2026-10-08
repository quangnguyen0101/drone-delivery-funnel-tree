#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dựng lại ĐƯỜNG ĐI ngắn nhất (polyline) từ funnel tree.

Port trung thành `/funnel_tree_example/algo/`:

    subFunnelTree  -> cây funnel cho một nguồn (giống algorithm1.py)
    FunnelTree     -> (1) geodesic thẳng nhất, (2) tìm đỉnh lõm,
                      (3) geodesic từ đỉnh lõm, (4) gộp lại,
                      (5) trải phẳng (unfold) ra các điểm trên mặt,
                      (6) nối các đoạn geodesic thành polyline

Ghi ra output/<tên>.geom, cùng định dạng với expected/:
    mỗi dòng  `m [x y z] [x y z] ...`  = đường đi từ nguồn tới đỉnh tương ứng.

Chạy:  python funnel_paths.py [--source S] [tên.geom ...]
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from algorithm1 import Mesh
from run import S, read_geom, source_for

INF = math.inf


def _angle3(ab2: float, bc2: float, ca2: float) -> float:
    cos = (ab2 + bc2 - ca2) / (math.sqrt(ab2 * bc2) * 2)
    return 0.0 if cos >= 1 else math.pi if cos <= -1 else math.acos(cos)


def _cal_pv2(pqv: float, pq2: float, qv2: float) -> float:
    return pq2 + qv2 - math.sqrt(pq2 * qv2) * math.cos(pqv) * 2


def _d2(mesh: Mesh, a: int, b: int) -> float:
    return mesh.dist(a, b) ** 2


@dataclass
class Funnel:
    p: int
    q: int
    x: int
    a: int                       # điểm neo khi trải phẳng
    sequence: list[int]          # các mặt từ cusp tới miệng funnel
    sp2: float; pq2: float
    spq: float; psw: float; pqv: float
    asp: float = 0.0


def sub_funnel_tree(mesh: Mesh, s: int) -> list[list[Funnel]]:
    """Cây funnel gốc s theo từng tầng (không có Thủ tục 2, giống )."""
    faces_at_s = mesh.vertex_faces[s]
    tree: list[list[Funnel]] = []
    root: list[Funnel] = []
    q = -1

    def insert(psq_index: int, p: int) -> None:
        nonlocal q
        t = mesh.triangles[psq_index]
        q = t[0] + t[1] + t[2] - s - p
        psq = mesh.angle(p, s, q)
        root.append(Funnel(p, q, p, p, [psq_index], _d2(mesh, s, p),
                           _d2(mesh, p, q), mesh.angle(s, p, q), psq, 0.0, 0.0))

    psq_index = faces_at_s[0]
    t = mesh.triangles[psq_index]
    p = t[0] if t[0] != s else t[1]
    insert(psq_index, p)
    for _ in range(1, len(faces_at_s)):
        ef = mesh.edge_faces[(s, q) if s < q else (q, s)]
        psq_index = ef[0] + ef[1] - psq_index
        insert(psq_index, q)

    tree.append(root)
    while tree[-1]:
        nxt: list[Funnel] = []
        for f in tree[-1]:
            while True:                       # goto find_v
                ef = mesh.edge_faces[min(f.x, f.q), max(f.x, f.q)]
                next_face = ef[0] + ef[1] - f.sequence[-1]
                if next_face in f.sequence:
                    break
                f.sequence.append(next_face)

                t = mesh.triangles[next_face]
                v = t[0] + t[1] + t[2] - f.x - f.q
                f.pqv += mesh.angle(f.x, f.q, v)
                vq2 = _d2(mesh, v, f.q)
                pv2 = _cal_pv2(f.pqv, f.pq2, vq2)
                vpq = _angle3(pv2, f.pq2, vq2) * (-1 if f.pqv > math.pi else 1)
                spv = f.spq + vpq

                if spv >= math.pi:            # funnel không có con
                    f.x = v
                    continue

                sv2 = _cal_pv2(spv, f.sp2, pv2)
                psv = _angle3(f.sp2, sv2, pv2)
                f.pqv = mesh.angle(f.x, v, f.q) + vpq + f.pqv - math.pi

                if psv >= f.psw:              # một con
                    f.q, f.pq2, f.spq = v, pv2, spv
                    continue

                vsw = f.psw - psv
                pvs = _angle3(pv2, sv2, f.sp2)
                svq = _angle3(pv2, vq2, f.pq2) - pvs
                nxt.append(Funnel(f.p, v, f.x, f.a, list(f.sequence),
                                  f.sp2, pv2, spv, psv, f.pqv, f.asp))
                nxt.append(Funnel(v, f.q, v, f.a, list(f.sequence),
                                  sv2, vq2, svq, vsw, 0.0, f.asp + psv))
                break
        tree.append(nxt)
    tree.pop()                                # bỏ tầng rỗng cuối
    return tree


@dataclass
class PathInfo:
    total_length: float
    curr_funnel: Funnel | None
    curr_s: int


def _generate_path_info(mesh: Mesh, s0: int,
                        trees: list) -> list[PathInfo]:
    trees.append(sub_funnel_tree(mesh, s0))
    infos = [PathInfo(INF, None, s0) for _ in mesh.points]
    infos[s0].total_length = 0.0
    for level in trees[-1]:
        for f in level:
            if infos[f.p].total_length > f.sp2:
                infos[f.p].total_length = f.sp2
                infos[f.p].curr_funnel = f
    for pi in infos:
        pi.total_length = math.sqrt(pi.total_length)
    return infos


def funnel_tree_paths(mesh: Mesh, s: int) -> list[list[tuple[float, float, float]]]:
    """Đường đi (danh sách điểm 3D) từ s tới mọi đỉnh."""
    trees: list = []
    path_infos = _generate_path_info(mesh, s, trees)

    concave = []
    for i in range(len(mesh.points)):
        if i == s:
            continue
        total = 0.0
        for j in mesh.vertex_faces[i]:
            t = mesh.triangles[j]
            a = t[0] if t[0] != i else t[1]
            b = t[0] + t[1] + t[2] - i - a
            total += mesh.angle(a, i, b)
        if total >= math.pi * 2 + 1e-5:
            concave.append(i)

    sub_infos = [_generate_path_info(mesh, i, trees) for i in concave]

    def update(j: int) -> None:
        for k, cv in enumerate(concave):
            length = path_infos[cv].total_length + sub_infos[k][j].total_length
            if path_infos[j].total_length > length:
                path_infos[j].total_length = length
                path_infos[j].curr_funnel = sub_infos[k][j].curr_funnel
                path_infos[j].curr_s = cv

    for _ in range(1, len(concave)):
        for j in concave:
            update(j)
    for j in range(len(mesh.points)):
        update(j)

    # bước 5: trải phẳng đường geodesic cuối cùng ra các điểm trên mặt
    pointpaths: list[list] = []
    for pi in path_infos:
        pp: list = []
        pointpaths.append(pp)
        f = pi.curr_funnel
        if f is None:
            continue
        pp.append(mesh.points[pi.curr_s])

        a, b, abc_id = f.a, pi.curr_s, f.sequence[0]
        ass2 = f.asp
        if a != f.p:
            while True:
                t = mesh.triangles[abc_id]
                c = t[0] + t[1] + t[2] - a - b
                if c == f.p:
                    break
                spt = pp[-1]
                pa, pc = mesh.points[a], mesh.points[c]
                ax, ay, az = pa[0] - spt[0], pa[1] - spt[1], pa[2] - spt[2]
                cx, cy, cz = pc[0] - spt[0], pc[1] - spt[1], pc[2] - spt[2]
                ma = ax * ax + ay * ay + az * az
                mc = cx * cx + cy * cy + cz * cz
                if ma <= 0.0 or mc <= 0.0:   # C++ ra NaN ở đây; ta chọn 0 cho an toàn
                    asc = 0.0
                else:
                    asc = math.acos(max(-1.0, min(1.0, (ax * cx + ay * cy + az * cz)
                                                  / math.sqrt(ma * mc))))
                if asc < ass2:
                    ass2 = math.pi - ass2
                    a, b = b, a
                new_ass2 = ass2 + mesh.angle(b, a, c)
                pba = mesh.points[a]
                as2 = (spt[0] - pba[0]) ** 2 + (spt[1] - pba[1]) ** 2 + (spt[2] - pba[2]) ** 2
                ac2 = _d2(mesh, a, c)
                b = c
                ratio = math.sqrt(as2 / ac2) * math.sin(ass2) / math.sin(new_ass2)
                ass2 = new_ass2
                ef = mesh.edge_faces[min(a, b), max(a, b)]
                abc_id = ef[0] + ef[1] - abc_id
                qa, qb = mesh.points[a], mesh.points[b]
                pp.append((ratio * qb[0] - (ratio - 1) * qa[0],
                           ratio * qb[1] - (ratio - 1) * qa[1],
                           ratio * qb[2] - (ratio - 1) * qa[2]))
        pp.append(mesh.points[f.p])

    # bước 6: nối đoạn geodesic từ đỉnh lõm vào đường cuối
    def add_points(p: int, target_s: int) -> None:
        curr_s = path_infos[p].curr_s
        if curr_s == target_s:
            return
        add_points(curr_s, target_s)
        pointpaths[p][:0] = pointpaths[curr_s][:-1]
        path_infos[p].curr_s = target_s

    for i in range(len(mesh.points)):
        add_points(i, s)
    pointpaths[s] = [mesh.points[s], mesh.points[s]]
    return pointpaths


def write_paths(path: Path, pointpaths) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for pts in pointpaths:
            fh.write(f"{len(pts)} ")
            for p in pts:
                fh.write(f"[{p[0]:.4f} {p[1]:.4f} {p[2]:.4f}] ")
            fh.write("\n")


def path_length(pts) -> float:
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def main() -> None:
    here = Path(__file__).parent
    ap = argparse.ArgumentParser(description="Sinh output/ (đường đi) từ funnel tree")
    ap.add_argument("files", nargs="*", help="tên file trong input/ (mặc định: tất cả)")
    ap.add_argument("-s", "--source", type=int, default=None,
                    help=f"đỉnh nguồn (mặc định theo bảng SOURCES của run.py, thường {S})")
    ap.add_argument("--check", action="store_true",
                    help="so độ dài đường đi với expected/ (nếu có)")
    a = ap.parse_args()

    files = sorted((here / "input").glob("*.geom"))
    if a.files:
        want = set(a.files)
        files = [f for f in files if f.name in want or str(f) in want]
    if not files:
        sys.exit("không có file .geom nào trong input/")

    worst = 0.0
    for f in files:
        mesh = read_geom(f)
        src = a.source if a.source is not None else source_for(f.name)
        pp = funnel_tree_paths(mesh, src)
        out = here / "output" / f.name
        write_paths(out, pp)
        msg = f"{f.name:18s} V={len(mesh.points):3d} s={src} -> {out}"
        exp_path = here / "expected" / f.name
        if a.check and exp_path.exists():
            from view_geom import read_paths
            exp = read_paths(exp_path)
            errs = sorted((abs(path_length(pp[v]) - path_length(exp[v])), v)
                          for v in range(len(mesh.points)))
            top = errs[0] if errs else (0.0, -1)
            worst = max(worst, top[0])
            msg += f"   |expected| lệch max={top[0]:.3g} tại {top[1]}"
        print(msg)
    if a.check:
        print(f"\nlệch lớn nhất so với output C++: {worst:.6g}")


if __name__ == "__main__":
    main()
