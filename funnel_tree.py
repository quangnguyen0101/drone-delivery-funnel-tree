#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thuật toán 1 — Funnel tree để tìm các đường đi ngắn nhất
========================================================

Hiện thực theo:


Mục 4.1 (Thuật toán 1) và Mục 3.3 (xác định con của một funnel, các PT (1)–(6)).

- Dữ liệu vào: bề mặt đa diện tam giác hoá + đỉnh nguồn s.
- Dữ liệu ra:  funnel tree gốc s, sinh theo từng tầng (level).

Đây là bản tối giản đúng như giả thiết của Mục 4.1:
    SP_S(v, p) = [v, p]   và   SP_S(p, q) = [p, q].
Trường hợp tổng quát (SP là đường gấp khúc) xem Hình 13 bài báo.

Chỗ cần nối Thủ tục 2 (Clip off Funnels) được đánh dấu bằng `clip`.
Nếu `clip = None`, thuật toán chạy như khi chưa xử lý "chiếm đỉnh v".

Phụ thuộc: chỉ stdlib.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

PI = math.pi
EPS = 1e-12


def _clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


def _law_cos_side(s1: float, s2: float, included: float) -> float:
    """Độ dài cạnh đối diện góc `included` của tam giác có hai cạnh s1, s2."""
    return math.sqrt(max(0.0, s1 * s1 + s2 * s2 - 2.0 * s1 * s2 * math.cos(included)))


def _angle_sss(opposite: float, s1: float, s2: float) -> float:
    """Góc đối diện cạnh `opposite` (định luật cos) khi biết ba cạnh s1, s2, opposite."""
    if s1 <= EPS or s2 <= EPS:
        return 0.0
    return math.acos(_clamp((s1 * s1 + s2 * s2 - opposite * opposite) / (2.0 * s1 * s2)))


# ---------------------------------------------------------------------------
# Bề mặt đa diện tam giác hoá
# ---------------------------------------------------------------------------

class Mesh:
    def __init__(self, points, triangles):
        self.points = [tuple(float(c) for c in p) for p in points]
        self.triangles = [tuple(int(v) for v in t) for t in triangles]
        self.vertex_faces: list[list[int]] = [[] for _ in self.points]
        self.edge_faces: dict[tuple[int, int], list[int]] = {}
        for fi, t in enumerate(self.triangles):
            for v in t:
                self.vertex_faces[v].append(fi)
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                key = (a, b) if a < b else (b, a)
                self.edge_faces.setdefault(key, []).append(fi)

    def dist(self, a: int, b: int) -> float:
        pa, pb = self.points[a], self.points[b]
        return math.sqrt(sum((pa[i] - pb[i]) ** 2 for i in range(3)))

    def angle(self, a: int, b: int, c: int) -> float:
        """Góc ∠abc tại đỉnh b."""
        pb, pa, pc = self.points[b], self.points[a], self.points[c]
        u = [pa[i] - pb[i] for i in range(3)]
        v = [pc[i] - pb[i] for i in range(3)]
        nu = math.sqrt(sum(x * x for x in u))
        nv = math.sqrt(sum(x * x for x in v))
        if nu <= EPS or nv <= EPS:
            return 0.0
        return math.acos(_clamp(sum(u[i] * v[i] for i in range(3)) / (nu * nv)))

    def other_face(self, a: int, b: int, face: int) -> int:
        """Mặt còn lại của cạnh [a, b] ngoài `face`."""
        faces = self.edge_faces[(a, b) if a < b else (b, a)]
        return faces[0] if faces[1] == face else faces[1]

    def third_vertex(self, tri_index: int, a: int, b: int) -> int:
        t = self.triangles[tri_index]
        return t[0] + t[1] + t[2] - a - b


# ---------------------------------------------------------------------------
# Funnel — một nút của funnel tree
# ---------------------------------------------------------------------------

@dataclass
class Funnel:
    """F_{p,q,S} với cusp s cố định.

    p, q : hai đầu miệng funnel, SP_S(p, q) = [p, q]
    x    : đỉnh đang xét, kề q (ban đầu x = p); mặt kế tiếp nằm trên cạnh [x, q]
    S    : dãy tam giác từ mặt chứa cusp đến mặt chứa miệng
    sp   : l(SP(s, p)) — độ dài left border
    pq   : l([p, q])
    spq  : ∠spq
    psw  : ∠psq — góc tại cusp giữa hai border
    pqv  : góc tích luỹ tại q từ [q, p] tới [q, x] (PT (4))
    level: tầng trong cây
    """
    p: int
    q: int
    x: int
    S: list[int]
    cusp: int
    sp: float
    pq: float
    spq: float
    psw: float
    pqv: float = 0.0
    level: int = 0
    parent: "Funnel | None" = None
    children: list["Funnel"] = field(default_factory=list)
    deleted: bool = False
    clip_l: float = 0.0          # l = |SP_{S∪△pqv}(s, v)| khi funnel sinh 2 con
    clip_angle: float = 0.0      # ∠pvz khi funnel sinh 2 con


@dataclass
class Tree:
    levels: list[list[Funnel]] = field(default_factory=list)
    # best[v]: |SP_S(s, v)| nhỏ nhất thấy được khi v là direct destination.
    # Nhánh "một con" của _expand biến v thành q mới rồi bỏ mất sv, nên phải ghi ở đây.
    best: list[float] = field(default_factory=list)
    occupied: dict[tuple[int, int, int], Funnel] = field(default_factory=dict)

    @property
    def nodes(self) -> list[Funnel]:
        return [f for level in self.levels for f in level]


def _make_funnel(mesh: Mesh, s: int, p: int, q: int, face: int, x: int) -> Funnel:
    return Funnel(
        p=p, q=q, x=x, S=[face], cusp=s,
        sp=mesh.dist(s, p), pq=mesh.dist(p, q),
        spq=mesh.angle(s, p, q), psw=mesh.angle(p, s, q),
    )


# ---------------------------------------------------------------------------
# Thuật toán 1
# ---------------------------------------------------------------------------

ClipFn = Callable[[Mesh, "Funnel", "Funnel", int, int, int], "list[str] | set[str]"]


def funnel_tree(mesh: Mesh, s: int, clip: ClipFn | None = None) -> Tree:
    """Dựng funnel tree gốc s.

    clip: hook nối Thủ tục 2. Được gọi khi một ∠pvq đã bị chiếm bởi funnel khác
          (f la F_{p,q,S} hien tai, other la F_{p,q,S1} da chiem):
              clip(mesh, f, other, p, q, v)
          Tra ve cac con can xoa, ghi bang chuoi:
              "A-left", "A-right"  -> con trai/phai cua f
              "B-left", "B-right"  -> con trai/phai cua other
          (xem funnel_funnel_clip_glue.py de noi truc tiep Thủ tục 2).
    """
    tree = Tree()
    tree.best = [math.inf] * len(mesh.points)
    tree.best[s] = 0.0

    # Dòng 2-4: mỗi cạnh [p, q] đối diện với s sinh một funnel con của gốc.
    faces_at_s = mesh.vertex_faces[s]
    first_face = faces_at_s[0]
    t = mesh.triangles[first_face]
    p = next(v for v in t if v != s)
    q = mesh.third_vertex(first_face, s, p)
    roots = [_make_funnel(mesh, s, p, q, first_face, x=p)]

    cur_face = first_face
    for _ in range(1, len(faces_at_s)):
        # đi vòng quanh s qua cạnh [s, q] đến mặt kế tiếp
        face = mesh.other_face(s, q, cur_face)
        t = mesh.triangles[face]
        p, q = q, mesh.third_vertex(face, s, q)
        roots.append(_make_funnel(mesh, s, p, q, face, x=p))
        cur_face = face

    tree.levels.append(roots)

    # Dòng 5-18: mở rộng theo từng tầng.
    level_index = 1
    while tree.levels[-1]:
        nxt: list[Funnel] = []
        for f in tree.levels[-1]:
            _expand(mesh, f, nxt, tree, clip, level_index)
        tree.levels.append(nxt)
        level_index += 1

    if tree.levels and not tree.levels[-1]:
        tree.levels.pop()
    return tree


def _expand(mesh: Mesh, f: Funnel, out: list[Funnel], tree: Tree,
            clip: ClipFn | None, level_index: int) -> None:
    """Mở rộng một funnel cho tới khi nó sinh con hoặc không còn con."""
    if f.deleted:
        return
    while True:
        # Dòng 9: mặt kế tiếp nằm trên cạnh [x, q].
        face = mesh.other_face(f.x, f.q, f.S[-1])
        if face in f.S:                       # tam giác kế thuộc S  ->  không có con
            return

        f.S = f.S + [face]
        v = mesh.third_vertex(face, f.x, f.q)

        # PT (4): beta_v
        f.pqv += mesh.angle(f.x, f.q, v)
        vq = mesh.dist(v, f.q)
        pv = _law_cos_side(f.pq, vq, f.pqv)
        vpq = _angle_sss(vq, pv, f.pq)        # ∠vpq
        if f.pqv > PI:
            vpq = -vpq
        beta_v = f.spq + vpq

        if beta_v >= PI:                      # (5) không thoả: đổi direct destination
            f.x = v
            continue

        sv = _law_cos_side(f.sp, pv, beta_v)
        psv = _angle_sss(pv, f.sp, sv)        # ∠psv

        if sv < tree.best[v]:                # v nằm trên left border của con sắp sinh
            tree.best[v] = sv

        # cập nhật góc tích luỹ cho con trái (q = v)
        f.pqv = mesh.angle(f.x, v, f.q) + vpq + f.pqv - PI

        if psv >= f.psw:                      # (6) không thoả -> một con F_{p,v}
            # q := v nên border phải là SP(s, v): góc cusp đổi từ ∠psq sang psv.
            # Giữ ∠psq cũ làm mọi lần so (6) từ tầng sau dùng góc sai.
            f.q, f.pq, f.spq, f.psw = v, pv, beta_v, psv
            continue

        # hai con F_{p,v} và F_{v,q}
        vsw = f.psw - psv
        pvs = _angle_sss(f.sp, pv, sv)
        svq = _angle_sss(f.pq, vq, pv) - pvs

        # Thủ tục 2 cần l = |SP_{S∪△pqv}(s,v)| = sv và ∠pvz = pvs (z nằm trên s'v)
        f.clip_l, f.clip_angle = sv, pvs

        child_left = Funnel(p=f.p, q=v, x=f.x, S=f.S, cusp=f.cusp,
                            sp=f.sp, pq=pv, spq=beta_v, psw=psv,
                            pqv=f.pqv, level=level_index, parent=f)
        child_right = Funnel(p=v, q=f.q, x=v, S=f.S, cusp=f.cusp,
                             sp=sv, pq=vq, spq=svq, psw=vsw,
                             pqv=0.0, level=level_index, parent=f)

        # Dòng 14-16: nếu ∠pvq đã bị chiếm -> Thủ tục 2 (Clip off Funnels).
        key = (f.p, f.q, v)
        deleted: set[str] = set()
        if key in tree.occupied and clip is not None:
            deleted = set(clip(mesh, f, tree.occupied[key], f.p, f.q, v))
        tree.occupied.setdefault(key, f)

        f.children = [child_left, child_right]
        if "A-left" in deleted:
            child_left.deleted = True
        if "A-right" in deleted:
            child_right.deleted = True

        other = tree.occupied.get(key)
        if other is not None and other is not f and other.children:
            for side, c in (("left", other.children[0]), ("right", other.children[1])):
                if "B-" + side in deleted:
                    c.deleted = True
                    if c in out:
                        out.remove(c)

        # ponytail: neu con cua `other` da duoc mo rong (other o tang truoc),
        # cay con cua no khong bi cat; can cay lai neu gap mesh lon.
        if not child_left.deleted:
            out.append(child_left)
        if not child_right.deleted:
            out.append(child_right)
        return


# ---------------------------------------------------------------------------
# Khoảng cách ngắn nhất tới mọi đỉnh (kết quả trực tiếp của cây)
# ---------------------------------------------------------------------------

def shortest_distances(mesh: Mesh, s: int, clip: ClipFn | None = None) -> list[float]:
    tree = funnel_tree(mesh, s, clip)
    dist = [math.inf] * len(mesh.points)
    dist[s] = 0.0
    for f in tree.nodes:
        if not f.deleted and f.sp < dist[f.p]:
            dist[f.p] = f.sp
    # Mỗi direct destination v gặp khi mở rộng đều là một điểm trên left border
    # của funnel sắp sinh (độ dài = sv). Nhánh "một con" nuốt mất v nên phải ghi ở đây.
    for v, x in enumerate(tree.best):
        if x < dist[v]:
            dist[v] = x
    return dist