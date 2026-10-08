#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Glue — nối Thủ tục 2 (Clip off Funnels) vào Thuật toán 1 (funnel tree).
=======================================================================

`clip_with_funnel_clip` là callback truyền cho `funnel_tree.funnel_tree(..., clip=...)`.

Với f = F_{p,q,S} và other = F_{p,q,S1} cùng chiếm đỉnh v: hai giá trị mà Thủ tục 2
cần là l = |SP_S(s,v)| và ∠pvz, Algorithm 1 đã tính sẵn khi sinh con và lưu vào
`f.clip_l`, `f.clip_angle` (tương tự cho other).
"""

from __future__ import annotations

import funnel_clip


def clip_with_funnel_clip(mesh, f, other, p, q, v):
    return ["%s-%s" % (who, side) for who, side in
            funnel_clip.clip_off_funnels((f.clip_l, f.clip_angle),
                                        (other.clip_l, other.clip_angle))]
