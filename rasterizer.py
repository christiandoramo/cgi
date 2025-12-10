# rasterizer.py
from typing import Tuple, Set, List, Dict
import math
import transform

Pixel = Tuple[int, int]

# Bresenham (mantido)
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

# Scanline (mantido, devolve pixels inteiros dentro do triângulo)
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

# Solução de planos (para interpolação 1/z etc.)
def solve_plane_coeffs(p1, p2, p3):
    # Solve A*x + B*y + C = v for three points
    (x1, y1, v1) = p1
    (x2, y2, v2) = p2
    (x3, y3, v3) = p3
    # compute determinant
    det = (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
    EPS = 1e-9
    if abs(det) < EPS:
        # degenerate; return a fallback plane that is constant = v1
        return (0.0, 0.0, v1)
    # Cramer's rule for A,B,C
    A = (v1*(y2 - y3) + v2*(y3 - y1) + v3*(y1 - y2)) / det
    B = (x1*(v2 - v3) + x2*(v3 - v1) + x3*(v1 - v2)) / det
    C = (x1*(y2*v3 - y3*v2) + x2*(y3*v1 - y1*v3) + x3*(y1*v2 - y2*v1)) / det
    return (A, B, C)

# compute normals per vertex (world)
def compute_vertex_normals_world(vertices: List[Tuple[float,float,float]], triangles: List[Tuple[int,int,int]]):
    n = len(vertices)
    normals = [ [0.0, 0.0, 0.0] for _ in range(n) ]
    counts = [0 for _ in range(n)]
    for (a,b,c) in triangles:
        A = vertices[a]; B = vertices[b]; C = vertices[c]
        ux = B[0]-A[0]; uy = B[1]-A[1]; uz = B[2]-A[2]
        vx = C[0]-A[0]; vy = C[1]-A[1]; vz = C[2]-A[2]
        nx = uy*vz - uz*vy
        ny = uz*vx - ux*vz
        nz = ux*vy - uy*vx
        mag = math.sqrt(nx*nx + ny*ny + nz*nz)
        if mag > 1e-12:
            nx/=mag; ny/=mag; nz/=mag
        for idx in (a,b,c):
            normals[idx][0] += nx
            normals[idx][1] += ny
            normals[idx][2] += nz
            counts[idx] += 1
    out = []
    for i in range(n):
        if counts[i] == 0:
            out.append((0.0, 0.0, 1.0))
            continue
        nx, ny, nz = normals[i]
        mag = math.sqrt(nx*nx + ny*ny + nz*nz)
        if mag < 1e-12:
            out.append((0.0, 0.0, 1.0))
        else:
            out.append((nx/mag, ny/mag, nz/mag))
    return out

# clamp util
def clamp255(v):
    return max(0, min(255, int(round(v))))

# phong shading per fragment (view coords)
def phong_shade_at_fragment(P_view, N, V_dir, lighting):
    Iamb = lighting["Iamb"]
    Ka = float(lighting["Ka"])
    Il = lighting["Il"]
    Pl_view = lighting["_Pl_view"]
    Kd = lighting["Kd"]
    Od = lighting["Od"]
    Ks = float(lighting["Ks"])
    eta = float(lighting["eta"])

    # L vector
    Lx = Pl_view[0] - P_view[0]; Ly = Pl_view[1] - P_view[1]; Lz = Pl_view[2] - P_view[2]
    Lmag = math.sqrt(Lx*Lx + Ly*Ly + Lz*Lz)
    if Lmag < 1e-9:
        L = (0.0, 0.0, 1.0)
    else:
        L = (Lx/Lmag, Ly/Lmag, Lz/Lmag)

    ndotl = N[0]*L[0] + N[1]*L[1] + N[2]*L[2]
    if ndotl < 0:
        ndotl = 0.0

    Rx = 2*ndotl*N[0] - L[0]; Ry = 2*ndotl*N[1] - L[1]; Rz = 2*ndotl*N[2] - L[2]
    Rmag = math.sqrt(Rx*Rx + Ry*Ry + Rz*Rz)
    if Rmag < 1e-9:
        R = (0.0,0.0,1.0)
    else:
        R = (Rx/Rmag, Ry/Rmag, Rz/Rmag)

    rdotv = R[0]*V_dir[0] + R[1]*V_dir[1] + R[2]*V_dir[2]
    if rdotv < 0:
        rdotv = 0.0
    spec_factor = (rdotv ** eta) if rdotv > 0 else 0.0

    out = [0.0,0.0,0.0]
    for c in range(3):
        Ia = Iamb[c] * Ka * Od[c]
        Id = Il[c] * Kd[c] * Od[c] * ndotl
        Is = Il[c] * Ks * spec_factor
        val = Ia + Id + Is
        out[c] = clamp255(val)
    return (out[0], out[1], out[2])

# main rasterize: retorna tri_pixels_map e framebuffer {(x,y):(r,g,b)}
def rasterize_mesh(triangles: List[Tuple[int,int,int]],
                   proj_results: List[Dict],
                   width: int, height: int,
                   vertices_world: List[Tuple[float,float,float]] = None,
                   basis: Dict = None,
                   lighting: Dict = None) -> Tuple[Dict[int, set], Dict[Pixel, Tuple[int,int,int]]]:
    tri_pixels = {}
    framebuffer: Dict[Pixel, Tuple[int,int,int]] = {}
    # z-buffer (height x width) inicializado com +inf
    zbuf = [ [float("inf")] * width for _ in range(height) ]

    # precompute normals (view)
    if vertices_world is not None and basis is not None:
        vnorms_world = compute_vertex_normals_world(vertices_world, triangles)
        vnorms_view = []
        for n in vnorms_world:
            nv = transform.world_to_view_vector(n, basis)
            mag = math.sqrt(nv[0]*nv[0] + nv[1]*nv[1] + nv[2]*nv[2])
            if mag < 1e-9:
                vnorms_view.append((0.0, 0.0, 1.0))
            else:
                vnorms_view.append((nv[0]/mag, nv[1]/mag, nv[2]/mag))
    else:
        vnorms_view = [ (0.0,0.0,1.0) for _ in proj_results ]

    # prepare lighting (compute Pl in view coords)
    if lighting is not None and basis is not None:
        lighting_local = lighting.copy()
        pl_world = lighting_local.get("Pl", (0.0, 0.0, 10.0))
        pl_view = transform.world_to_view_point(pl_world, basis)
        lighting_local["_Pl_view"] = pl_view
    else:
        lighting_local = lighting or {}

    for ti, (a,b,c) in enumerate(triangles):
        if a < 0 or b < 0 or c < 0 or a >= len(proj_results) or b >= len(proj_results) or c >= len(proj_results):
            tri_pixels[ti] = set(); continue
        ra = proj_results[a]; rb = proj_results[b]; rc = proj_results[c]
        pa = ra.get("pixel", (None, None)); pb = rb.get("pixel", (None, None)); pc = rc.get("pixel", (None, None))
        vis_a = ra.get("visible", False); vis_b = rb.get("visible", False); vis_c = rc.get("visible", False)
        if pa[0] is None or pb[0] is None or pc[0] is None or not (vis_a and vis_b and vis_c):
            tri_pixels[ti] = set(); continue

        # quick reject degenerate area in screen space: cross of edges
        x1,y1 = float(pa[0]), float(pa[1])
        x2,y2 = float(pb[0]), float(pb[1])
        x3,y3 = float(pc[0]), float(pc[1])
        area2 = (x2-x1)*(y3-y1) - (y2-y1)*(x3-x1)
        if abs(area2) < 1e-3:
            tri_pixels[ti] = set(); continue

        pixels = rasterize_triangle_pixels(pa, pb, pc, width, height)
        tri_pixels[ti] = pixels
        if not pixels:
            continue

        A_view = ra["view"]; B_view = rb["view"]; C_view = rc["view"]
        Zv_a = A_view[2]; Zv_b = B_view[2]; Zv_c = C_view[2]
        if Zv_a == 0 or Zv_b == 0 or Zv_c == 0:
            continue
        invz_a = 1.0 / Zv_a; invz_b = 1.0 / Zv_b; invz_c = 1.0 / Zv_c

        # attributes for perspective-correct interpolation
        Xa_over_z = A_view[0] * invz_a; Ya_over_z = A_view[1] * invz_a
        Xb_over_z = B_view[0] * invz_b; Yb_over_z = B_view[1] * invz_b
        Xc_over_z = C_view[0] * invz_c; Yc_over_z = C_view[1] * invz_c

        Na = vnorms_view[a]; Nb = vnorms_view[b]; Nc = vnorms_view[c]
        nax = Na[0]*invz_a; nay = Na[1]*invz_a; naz = Na[2]*invz_a
        nbx = Nb[0]*invz_b; nby = Nb[1]*invz_b; nbz = Nb[2]*invz_b
        ncx = Nc[0]*invz_c; ncy = Nc[1]*invz_c; ncz = Nc[2]*invz_c

        # build plane coeffs (A*x + B*y + C)
        invz_coeffs = solve_plane_coeffs((x1,y1,invz_a),(x2,y2,invz_b),(x3,y3,invz_c))
        x_over_z_coeffs = solve_plane_coeffs((x1,y1,Xa_over_z),(x2,y2,Xb_over_z),(x3,y3,Xc_over_z))
        y_over_z_coeffs = solve_plane_coeffs((x1,y1,Ya_over_z),(x2,y2,Yb_over_z),(x3,y3,Yc_over_z))
        nx_over_z_coeffs = solve_plane_coeffs((x1,y1,nax),(x2,y2,nbx),(x3,y3,ncx))
        ny_over_z_coeffs = solve_plane_coeffs((x1,y1,nay),(x2,y2,nby),(x3,y3,ncy))
        nz_over_z_coeffs = solve_plane_coeffs((x1,y1,naz),(x2,y2,nbz),(x3,y3,ncz))

        A_invz, B_invz, C_invz = invz_coeffs
        A_xoz, B_xoz, C_xoz = x_over_z_coeffs
        A_yoz, B_yoz, C_yoz = y_over_z_coeffs
        A_nxoz, B_nxoz, C_nxoz = nx_over_z_coeffs
        A_nyoz, B_nyoz, C_nyoz = ny_over_z_coeffs
        A_nzoz, B_nzoz, C_nzoz = nz_over_z_coeffs

        for (px, py) in pixels:
            sx = px + 0.5; sy = py + 0.5
            invz = A_invz * sx + B_invz * sy + C_invz
            # safety checks to avoid NaN/inf and tiny invz
            if not math.isfinite(invz) or invz <= 1e-6:
                continue
            Zv = 1.0 / invz
            if py < 0 or py >= height or px < 0 or px >= width:
                continue
            if Zv >= zbuf[py][px]:
                continue

            x_over_z = A_xoz * sx + B_xoz * sy + C_xoz
            y_over_z = A_yoz * sx + B_yoz * sy + C_yoz
            Xv = x_over_z / invz
            Yv = y_over_z / invz
            P_view = (Xv, Yv, Zv)

            nx_over_z = A_nxoz * sx + B_nxoz * sy + C_nxoz
            ny_over_z = A_nyoz * sx + B_nyoz * sy + C_nyoz
            nz_over_z = A_nzoz * sx + B_nzoz * sy + C_nzoz
            nx = nx_over_z / invz; ny = ny_over_z / invz; nz = nz_over_z / invz
            nmag = math.sqrt(nx*nx + ny*ny + nz*nz)
            if not math.isfinite(nmag) or nmag < 1e-9:
                N = (0.0, 0.0, 1.0)
            else:
                N = (nx/nmag, ny/nmag, nz/nmag)

            Vdir = (-P_view[0], -P_view[1], -P_view[2])
            vmag = math.sqrt(Vdir[0]*Vdir[0] + Vdir[1]*Vdir[1] + Vdir[2]*Vdir[2])
            if not math.isfinite(vmag) or vmag < 1e-9:
                Vunit = (0.0, 0.0, 1.0)
            else:
                Vunit = (Vdir[0]/vmag, Vdir[1]/vmag, Vdir[2]/vmag)

            color = (255,255,255)
            if lighting_local is not None:
                try:
                    color = phong_shade_at_fragment(P_view, N, Vunit, lighting_local)
                except Exception:
                    # fallback color se Phong falhar
                    color = (0,0,0)

            framebuffer[(px, py)] = color
            zbuf[py][px] = Zv

    return tri_pixels, framebuffer
