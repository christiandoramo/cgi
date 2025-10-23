# rasterizer.py
from typing import Tuple, Set, List, Dict
import math

Pixel = Tuple[int, int]
Vec2f = Tuple[float, float]

def _edge_intersection_x(y: int, x0: float, y0: float, x1: float, y1: float) -> float:
    t = (y - y0) / (y1 - y0)
    return x0 + t * (x1 - x0)

def rasterize_triangle_pixels(p0: Tuple[float,int], p1: Tuple[float,int], p2: Tuple[float,int],
                              width: int, height: int) -> Set[Pixel]:
    verts = [(float(p0[0]), float(p0[1])),
             (float(p1[0]), float(p1[1])),
             (float(p2[0]), float(p2[1]))]

    ys = [v[1] for v in verts]

    min_y = math.ceil(max(min(ys), 0))
    max_y = math.floor(min(max(ys), height - 1))

    pixels = set()
    edges = [ (verts[0], verts[1]), (verts[1], verts[2]), (verts[2], verts[0]) ]

    for y in range(min_y, max_y + 1):
        inter_xs: List[float] = []
        for (xa, ya), (xb, yb) in edges:
            if abs(yb - ya) < 1e-9:
                continue
            ymin = min(ya, yb)
            ymax = max(ya, yb)
            # incluindo limites de forma consistente
            if y >= math.ceil(ymin) and y <= math.floor(ymax):
                x_int = _edge_intersection_x(y, xa, ya, xb, yb)
                inter_xs.append(x_int)
        if not inter_xs:
            continue
        inter_xs.sort()
        if len(inter_xs) % 2 != 0:
            inter_xs = inter_xs[:-1]
            if not inter_xs:
                continue
        for i in range(0, len(inter_xs), 2):
            x_left = inter_xs[i]
            x_right = inter_xs[i+1]
            x_start = math.ceil(min(x_left, x_right))
            x_end = math.floor(max(x_left, x_right))
            if x_end < 0 or x_start > width - 1:
                continue
            x_start = max(x_start, 0)
            x_end = min(x_end, width - 1)
            for x in range(x_start, x_end + 1):
                pixels.add((x, y))
    return pixels

def rasterize_mesh(triangles: List[Tuple[int,int,int]],
                   proj_results: List[Dict],
                   width: int, height: int) -> Dict[int, Set[Pixel]]:
    tri_pixels = {}
    for ti, (a,b,c) in enumerate(triangles):
        if a < 0 or b < 0 or c < 0:
            tri_pixels[ti] = set(); continue
        if a >= len(proj_results) or b >= len(proj_results) or c >= len(proj_results):
            tri_pixels[ti] = set(); continue
        ra = proj_results[a]; rb = proj_results[b]; rc = proj_results[c]
        pa = ra.get("pixel", (None, None)); pb = rb.get("pixel", (None, None)); pc = rc.get("pixel", (None, None))
        vis_a = ra.get("visible", False); vis_b = rb.get("visible", False); vis_c = rc.get("visible", False)
        # Exigir projetáveis e visíveis (simplificação)
        if pa[0] is None or pb[0] is None or pc[0] is None or not (vis_a and vis_b and vis_c):
            tri_pixels[ti] = set()
            continue
        pixels = rasterize_triangle_pixels(pa, pb, pc, width, height)
        tri_pixels[ti] = pixels
    return tri_pixels

# --- utilitário Bresenham para desenhar arestas (contorno) ---
def bresenham_line_pixels(x0, y0, x1, y1) -> List[Pixel]:
    x0 = int(round(x0)); y0 = int(round(y0))
    x1 = int(round(x1)); y1 = int(round(y1))
    pixels = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pixels.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pixels
