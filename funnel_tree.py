#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tính khoảng cách ngắn nhất từ nguồn đến các đỉnh bằng Funnel Tree.

Thuật toán 1: sinh funnel tree từ nguồn trên bề mặt đa diện tam giác hoá.
Có thể kết hợp với Thủ tục 2 (qua hàm clip) để cắt bỏ funnel không cần thiết.

Chỉ phụ thuộc stdlib.
"""

from __future__ import annotations


import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

PI = math.pi
EPS = 1e-12

# Đỉnh nguồn mặc định theo từng mesh (input/*.geom), nguồn chung S = 1.
S = 1
SOURCES: dict[str, int] = {"cube": 4, "icosahedron": 0, "star": 0, "dome": 17, "terrain": 24}


def source_for(name: str) -> int:
    return SOURCES.get(Path(name).stem, S)


def read_geom(path: str | Path) -> "Mesh":
    """Đọc file .geom: dòng đầu `V F E`, rồi V dòng điểm, rồi F dòng `3 a b c`."""
    lines = Path(path).read_text().splitlines()
    v, f, _ = (int(x) for x in lines[0].split()[:3])
    pts = [tuple(float(x) for x in lines[i + 1].split()[:3]) for i in range(v)]
    tris = []
    for i in range(f):
        t = tuple(int(x) for x in lines[v + 1 + i].split()[-3:])
        tris.append(t)
    return Mesh(pts, tris)


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
# Lớp biểu diễn lưới tam giác
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

    def other_face(self, a: int, b: int, face: int) -> int | None:
        """Mặt còn lại của cạnh [a, b] ngoài `face`; `None` nếu cạnh biên."""
        faces = self.edge_faces[(a, b) if a < b else (b, a)]
        if len(faces) == 1:
            return None
        return faces[0] if faces[1] == face else faces[1]

    @property
    def is_closed(self) -> bool:
        """Polytope kín: mọi cạnh đều có đúng 2 mặt (không có cạnh biên)."""
        return all(len(f) == 2 for f in self.edge_faces.values())

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
    pqv  : góc tích luỹ tại q từ [q, p] tới [q, x]
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


def _default_clip(mesh: Mesh, f: "Funnel", other: "Funnel",
                  p: int, q: int, v: int) -> set[str]:
    """Thủ tục 2 giản lược: giữ funnel có l = |SP(s,v)| ngắn hơn.

    Khác bản funnel_clip.py ở chỗ hòa hoàn toàn (l bằng và góc bằng): bản gốc
    trả [] -> giữ cả hai funnel, cây nhân đôi mỗi tầng -> nổ trên lưới đối xứng.
    Hai funnel đó là tương đương nên xoá funnel tới sau là an toàn.
    """
    l, a = f.clip_l, f.clip_angle
    l1, a1 = other.clip_l, other.clip_angle
    if l < l1:
        if a > a1:
            return {"B-right"}
        if a < a1:
            return {"B-left"}
    elif l1 < l:
        if a > a1:
            return {"A-left"}
        if a < a1:
            return {"A-right"}
    else:
        if a > a1:
            return {"A-left", "B-right"}
        if a < a1:
            return {"A-right", "B-left"}
    return {"A-left", "A-right"}


def _make_funnel(mesh: Mesh, s: int, p: int, q: int, face: int, x: int) -> Funnel:
    return Funnel(
        p=p, q=q, x=x, S=[face], cusp=s,
        sp=mesh.dist(s, p), pq=mesh.dist(p, q),
        spq=mesh.angle(s, p, q), psw=mesh.angle(p, s, q),
    )


# ---------------------------------------------------------------------------
# Thuật toán 1 — Funnel tree để tìm các đường đi ngắn nhất
# (Nguồn: "Bản dịch - Funnel Tree (bản đăng tạp chí).md", mục 4.1)
#
#  1:  root := s
#  2:  For mỗi cạnh [p, q] đối diện với s:
#  3:     Set S = △spq
#  4:     Chèn F_{p,q,S} làm con của root.
#  5:  While k ≤ n và tầng thứ k có nút:              ⊲ n là số mặt
#  6:     For mỗi funnel (nút) F_{p,q,S} tại tầng thứ k:
#  7:        Gọi v = v_j = direct destination của funnel F_{p,q,S} và β_v được xác định bởi (4).
#  8:        While β_v < π                            ⊲ tức là (5) được thỏa
#  9:           Lấy dãy S' các tam giác liền kề của polytope nằm giữa
#            [p, q] và [q, v] có hai cạnh kề tại q.
# 10:          Set S' := S ∪ △pqv.
# 11:          Nếu các funnel F_{p,v,S'}(t₁) và F_{v,q,S'}(t₂) có cùng cusp s
#              (tức là s = t₁ = t₂) và (6) được thỏa
# 12:             Then F_{p,q,S} có hai con F_{p,v,S'}, F_{v,q,S'}
# 13:             Chèn các con mà F_{p,q,S} có thể có như sau
# 14:               Nếu ∠pvq trước đó được đánh dấu bởi một funnel khác gọi là F_{p,q,S₁}
# 15:                  Then gọi Thủ tục Clip off Funnels(△pqv, S, S₁)
#                        ⊲ Thủ tục này dùng các kết luận 2)-4) của Bổ đề A.3 để xác định đứa con đó
# 16:             Chèn cả hai con của F_{p,q,S} vào funnel tree và đánh dấu ∠pvq
# 17:          Else, F_{p,q,S} có một con, chèn con đó vào funnel tree.
# 18:  k += 1
#
#   (3)  β_v := ∠spq + ∠vpq
#   (4)  β_v := ∠spq + arcsin( |vq|·sin(Σ∠v_i q v_{i+1}) / √(|vq|²+|pq|²-2|vq||pq|cos(Σ∠v_i q v_{i+1})) )
#   (5)  β_v < π   — funnel có phần trong tương đối không rỗng (còn con)
#   (6)  ∠psv < ∠psw — funnel có hai con; ngược lại chỉ một con F_{v,p}
#
# Các dòng trên được đánh dấu tương ứng ngay trong _expand() bên dưới.
# ---------------------------------------------------------------------------

ClipFn = Callable[[Mesh, "Funnel", "Funnel", int, int, int], "list[str] | set[str]"]


# ---------------------------------------------------------------------------
# Fan quanh nguồn (dòng 2-4 của Thuật toán 1) — khác nhau giữa kín và hở.
#
# KÍN (polytope đóng, Thuật toán 1 gốc): quét một chiều quanh s, đủ một vòng
#   (gặp lại first_face). Mỗi cạnh [p, q] đối diện s sinh một funnel con gốc.
# HỞ (bề mặt có biên): quét hai hướng từ first_face, dừng ở cạnh biên
#   (other_face = None). Fan là một dải không khép kín.
# ---------------------------------------------------------------------------


def _fan_closed(mesh: Mesh, s: int) -> list[tuple[int, int, int]]:
    """Fan quanh s trên polytope kín: một chiều, đủ một vòng quanh s."""
    first_face = mesh.vertex_faces[s][0]
    t = mesh.triangles[first_face]
    p = next(v for v in t if v != s)
    q = mesh.third_vertex(first_face, s, p)
    fan: list[tuple[int, int, int]] = [(first_face, p, q)]
    cur_face = first_face
    while True:
        face = mesh.other_face(s, q, cur_face)
        if face is None or face == first_face:
            break
        p, q = q, mesh.third_vertex(face, s, q)
        fan.append((face, p, q))
        cur_face = face
    return fan


def _fan_open(mesh: Mesh, s: int) -> list[tuple[int, int, int]]:
    """Fan quanh s trên bề mặt hở: quét thuận, rồi quét ngược, dừng ở biên."""
    first_face = mesh.vertex_faces[s][0]
    t = mesh.triangles[first_face]
    p = next(v for v in t if v != s)
    q = mesh.third_vertex(first_face, s, p)
    fan: list[tuple[int, int, int]] = [(first_face, p, q)]
    cur_face = first_face
    while True:
        face = mesh.other_face(s, q, cur_face)
        if face is None or face == first_face:
            break
        p, q = q, mesh.third_vertex(face, s, q)
        fan.append((face, p, q))
        cur_face = face
    back: list[tuple[int, int, int]] = []
    cur_face, p0, q0 = first_face, fan[0][1], fan[0][2]
    while True:
        face = mesh.other_face(s, p0, cur_face)
        if face is None or face == first_face:
            break
        p1 = mesh.third_vertex(face, s, p0)
        back.append((face, p1, p0))
        cur_face, p0 = face, p1
    return back[::-1] + fan


def _fan(mesh: Mesh, s: int) -> list[tuple[int, int, int]]:
    return _fan_closed(mesh, s) if mesh.is_closed else _fan_open(mesh, s)


def funnel_tree(mesh: Mesh, s: int, clip: ClipFn | None = None) -> Tree:
    """Dựng funnel tree gốc s.

    Áp dụng Thuật toán 1 cho cả polytope kín và bề mặt hở. Khác nhau duy
    nhất ở (i) fan quanh s — kín quét một vòng, hở quét hai hướng dừng ở
    biên (xem _fan_closed/_fan_open); (ii) điểm dừng của funnel trong
    _expand — hở dừng sớm khi gặp cạnh biên (other_face = None). Các metric
    (3)-(6), clip (Thủ tục 2) và cấu trúc đánh dấu ∠pvw không đổi.

    clip: hook nối Thủ tục 2. Được gọi khi một ∠pvq đã bị chiếm bởi funnel khác
          (f la F_{p,q,S} hien tai, other la F_{p,q,S1} da chiem):
              clip(mesh, f, other, p, q, v)
          Tra ve cac con can xoa, ghi bang chuoi:
              "A-left", "A-right"  -> con trai/phai cua f
              "B-left", "B-right"  -> con trai/phai cua other
          (xem funnel_ de noi truc tiep Thủ tục 2).
    """
    tree = Tree()
    tree.best = [math.inf] * len(mesh.points)
    tree.best[s] = 0.0

    # Dòng 2-4: mỗi cạnh [p, q] đối diện với s sinh một funnel con của gốc.
    # Kín: quét một vòng quanh s. Hở: quét hai hướng, dừng ở cạnh biên.
    fan = _fan(mesh, s)
    roots = [_make_funnel(mesh, s, fp, fq, face, x=fp) for face, fp, fq in fan]

    # Bề mặt hở: q của funnel gốc chót (cạnh biên) không bao giờ thành p của funnel nào.
    # Với kín, đỉnh nào cũng là p hoặc v của funnel nào đó nên best[] đã được ghi đủ.
    for root in roots:
        dq = mesh.dist(s, root.q)
        if dq < tree.best[root.q]:
            tree.best[root.q] = dq

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
    """Mở rộng một funnel — thân vòng For của Thuật toán 1 (dòng 6-17).

    while duyệt từng direct destination v của funnel; mỗi v là đỉnh còn lại của
    tam giác kế tiếp nằm trên cạnh [x, q]. Với mỗi v:
    - β_v >= PI  -> (5) không thoả: F không có con tại v (Bổ đề A.4: bỏ qua v).
    - (6) thoả   -> F có hai con F_{p,v}, F_{v,q} (dòng 12-16), funnel kết thúc.
    - (6) không  -> F có một con F_{p,v} (dòng 17), funnel tiếp tục quét.
    """
    if f.deleted:
        return

    # Dòng 8: While β_v < PI — vòng duyệt các direct destination của funnel.
    while True:
        # Dòng 9: tam giác kế tiếp của polytope trên cạnh [x, q], hai cạnh kề tại q.
        face = mesh.other_face(f.x, f.q, f.S[-1])
        if face is None or face in f.S:
            # Chú thích Thuật toán 1: tam giác kế thuộc S (hoặc cạnh biên) -> F không có con.
            return

        # Dòng 10: S' := S ∪ △pqv, với v là direct destination mới.
        f.S = f.S + [face]
        v = mesh.third_vertex(face, f.x, f.q)

        # Dòng 7: β_v theo (3)-(4) — dùng luật cos (1) thay cho arccos trong (4):
        # góc tích luỹ tại q từ [q,p] tới [q,v] rồi cộng ∠spq.
        f.pqv += mesh.angle(f.x, f.q, v)           # Σ ∠v_i q v_{i+1}
        vq = mesh.dist(v, f.q)
        pv = _law_cos_side(f.pq, vq, f.pqv)        # (1): |ca| theo |vq|, |pq|, Σ góc tại q
        vpq = _angle_sss(vq, pv, f.pq)             # (2): ∠vpq
        if f.pqv > PI:
            vpq = -vpq
        beta_v = f.spq + vpq                       # (3)

        if beta_v >= PI:
            # Dòng 8: (5) không thoả -> F không có con tại v.
            # Bổ đề A.4: bỏ qua v (S' đã ∪ △pqv), sang direct destination kế tiếp.
            # (bổ trợ) best[]: v nằm sau p trên biên trái, |SP(s,v)| = sp + pv.
            if f.sp + pv < tree.best[v]:
                tree.best[v] = f.sp + pv
            f.x = v
            continue

        sv = _law_cos_side(f.sp, pv, beta_v)
        psv = _angle_sss(pv, f.sp, sv)             # ∠psv

        # (bổ trợ) best[]: v nằm trên left border của con sắp sinh, |SP(s,v)| = sv.
        if sv < tree.best[v]:
            tree.best[v] = sv

        # Dòng 11: kiểm tra (6); con trái F_{p,v} cần góc tích luỹ quay về phía [q,v].
        f.pqv = mesh.angle(f.x, v, f.q) + vpq + f.pqv - PI

        if psv >= f.psw:
            # Dòng 17: (6) không thoả -> F có một con, là chính funnel này tiếp tục
            # quét với q := v. ∠psw mới = psv để các so (6) sau dùng góc cusp đúng.
            f.q, f.pq, f.spq, f.psw = v, pv, beta_v, psv
            continue

        # Dòng 12: F_{p,v,S'}(t1) và F_{v,q,S'}(t2) cùng cusp s (bất biến của cây:
        # mọi funnel đều cusp s) và (6) thoả -> F có hai con F_{p,v}, F_{v,q}.
        vsw = f.psw - psv
        pvs = _angle_sss(f.sp, pv, sv)
        svq = _angle_sss(f.pq, vq, pv) - pvs

        # Dữ liệu cho Thủ tục 2 (Bổ đề A.3): l = |SP_{S'}(s,v)| (= sv), ∠pvz = pvs.
        f.clip_l, f.clip_angle = sv, pvs

        child_left = Funnel(p=f.p, q=v, x=f.x, S=f.S, cusp=f.cusp,
                            sp=f.sp, pq=pv, spq=beta_v, psw=psv,
                            pqv=f.pqv, level=level_index, parent=f)
        child_right = Funnel(p=v, q=f.q, x=v, S=f.S, cusp=f.cusp,
                             sp=sv, pq=vq, spq=svq, psw=vsw,
                             pqv=0.0, level=level_index, parent=f)

        # Dòng 14-16: nếu ∠pvq đã bị funnel khác F_{p,q,S1} chiếm -> Thủ tục 2
        # (Clip off Funnels) quyết định con nào bị xoá; rồi chèn cả hai con
        # vào funnel tree và đánh dấu ∠pvq.
        key = (f.p, f.q, v)
        deleted: set[str] = set()
        other: Funnel | None = tree.occupied.get(key)
        if other is not None:
            if clip is None:
                deleted = _default_clip(mesh, f, other, f.p, f.q, v)
                # funnel mới hơn hẳn -> nó thay other làm gốc của wedge này
                if f.clip_l < other.clip_l:
                    tree.occupied[key] = f
            else:
                deleted = set(clip(mesh, f, other, f.p, f.q, v))
        tree.occupied.setdefault(key, f)          # đánh dấu ∠pvq (dòng 16)

        f.children = [child_left, child_right]
        if "A-left" in deleted:
            child_left.deleted = True
        if "A-right" in deleted:
            child_right.deleted = True

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


# ---------------------------------------------------------------------------
# Tự kiểm tra: bề mặt mở (mặt phẳng grid) phải cho khoảng cách khớp Euclid.
# Bề mặt kín không có tham chiếu C++ ở đây; chạy funnel_paths.py cho bộ .geom.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    def flat_grid(n: int) -> Mesh:
        pts = [(x, y, 0.0) for y in range(n) for x in range(n)]
        tris = []
        for y in range(n - 1):
            for x in range(n - 1):
                a = y * n + x
                tris += [(a, a + 1, a + n), (a + 1, a + n + 1, a + n)]
        return Mesh(pts, tris)

    import math

    ok = True
    for n in (4, 8, 12, 16):
        m = flat_grid(n)
        for s in (0, n - 1, n * (n - 1), n * n - 1, n * n // 2):
            d = shortest_distances(m, s)
            if any(math.isinf(x) for x in d):
                print(f"FAIL: n={n} s={s}: có đỉnh không tới được")
                ok = False
                continue
            err = max(abs(d[i] - math.dist(m.points[s], m.points[i]))
                      for i in range(n * n))
            if err > 1e-4:
                print(f"FAIL: n={n} s={s}: sai số {err:.3g}")
                ok = False

    # Polytope hở: dome = mảnh vỏ cầu (đáy hở, 8 cạnh biên). Mọi đỉnh trên
    # bề mặt lồi hở đều phải tới được từ s=17 (nguồn trên vành biên).
    here = Path(__file__).parent
    dome = here / "input" / "dome.geom"
    if dome.exists():
        md = read_geom(dome)
        dd = shortest_distances(md, source_for("dome.geom"))
        if any(math.isinf(x) for x in dd):
            print("FAIL: dome có đỉnh không tới được")
            ok = False

    print("PASS: bề mặt mở khớp Euclid" if ok else "FAIL")