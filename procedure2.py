#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thủ tục 2 — Clip off Funnels
============================

Hiện thực theo:

  Phan Thanh An, Tran Van Hoai & Vuong Ba Thinh (2024).
  "The funnel tree algorithm for finding shortest paths on polyhedral surfaces."
  Optimization, 73(13), 4011-4036.  DOI: 10.1080/02331934.2023.2241496

Cho hai funnel F_{p,q,S} và F_{p,q,S1} cùng cusp s, cùng chiếm đỉnh v của dãy
△pqv. Gọi:
    l,  l1       : |SP_S(s, v)| và |SP_{S1}(s, v)|
    ∠pvz, ∠pvz1  : góc tại v giữa [v, p] và [v, z] (z = giao của SP(s, v) với [p, q])

KHÔNG cần trải phẳng để tính l và ∠pvz: chúng chính là `sv` và `pvs` mà Algorithm 1
đã tính sẵn bằng định luật cos (PT (1)–(2)), vì z nằm trên đoạn thẳng s'v nên
∠pvz = ∠pvs. Vì vậy thủ tục này chỉ nhận hai cặp (l, ∠pvz).

Trả về các con cần xóa theo Bổ đề A.3, dạng (funnel, kiểu):
    funnel ∈ {'A','B'} (A = F_{p,q,S}, B = F_{p,q,S1})
    kiểu   ∈ {'left','right'} với left = F_{p,v,*}, right = F_{v,q,*}
"""

from __future__ import annotations


def clip_off_funnels(measA: tuple[float, float], measB: tuple[float, float]) -> list[tuple[str, str]]:
    l, a = measA
    l1, a1 = measB

    if l < l1:                                   # Bổ đề A.3 2): giữ con của A
        if a > a1:
            return [("B", "right")]
        if a < a1:
            return [("B", "left")]
    elif l1 < l:                                 # Bổ đề A.3 3): giữ con của B
        if a > a1:
            return [("A", "left")]
        if a < a1:
            return [("A", "right")]
    else:                                        # Bổ đề A.3 4): hòa
        if a > a1:
            return [("A", "left"), ("B", "right")]
        if a < a1:
            return [("A", "right"), ("B", "left")]
    return []
