# rasterizer.py
from typing import Tuple, Set, List, Dict
import math
import numpy as np
import transform

Pixel = Tuple[int,int]

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

def compute_vertex_normals_world(vertices: List[Tuple[float,float,float]], triangles: List[Tuple[int,int,int]]):
    n = len(vertices)
    normals = [ [0.0,0.0,0.0] for _ in range(n) ]
    counts = [0]*n
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
            out.append((0.0,0.0,1.0))
            continue
        nx, ny, nz = normals[i]
        mag = math.sqrt(nx*nx + ny*ny + nz*nz)
        if mag < 1e-12:
            out.append((0.0,0.0,1.0))
        else:
            out.append((nx/mag, ny/mag, nz/mag))
    return out

def clamp_uint8(arr):
    arr = np.clip(arr, 0, 255)
    return arr.astype(np.uint8)

def phong_shade_vectorized(Px, Py, Pz, Nx, Ny, Nz, light_view, lighting):
    """
    Inputs are 2D arrays (or flattened 1D) of same shape, or scalars.
    Returns (R,G,B) arrays uint8.
    lighting: dict with Iamb, Ka, Il, Kd, Od, Ks, eta
    """
    # convert to numpy arrays
    Px = np.asarray(Px); Py = np.asarray(Py); Pz = np.asarray(Pz)
    Nx = np.asarray(Nx); Ny = np.asarray(Ny); Nz = np.asarray(Nz)

    # normalize normals (safety)
    nmag = np.sqrt(Nx*Nx + Ny*Ny + Nz*Nz)
    nmag = np.where(nmag < 1e-9, 1.0, nmag)
    Nx = Nx / nmag; Ny = Ny / nmag; Nz = Nz / nmag

    # V direction = -P (camera at origin in view coords)
    Vx = -Px; Vy = -Py; Vz = -Pz
    vmag = np.sqrt(Vx*Vx + Vy*Vy + Vz*Vz)
    vmag = np.where(vmag < 1e-9, 1.0, vmag)
    Vx = Vx / vmag; Vy = Vy / vmag; Vz = Vz / vmag

    # L vector (to light) = Pl_view - P_view
    Plx, Ply, Plz = light_view
    Lx = Plx - Px; Ly = Ply - Py; Lz = Plz - Pz
    lmag = np.sqrt(Lx*Lx + Ly*Ly + Lz*Lz)
    lmag = np.where(lmag < 1e-9, 1.0, lmag)
    Lx = Lx / lmag; Ly = Ly / lmag; Lz = Lz / lmag

    # N dot L
    ndotl = Nx*Lx + Ny*Ly + Nz*Lz
    ndotl = np.maximum(ndotl, 0.0)

    # Reflection R = 2(N·L)N - L
    Rx = 2*ndotl*Nx - Lx
    Ry = 2*ndotl*Ny - Ly
    Rz = 2*ndotl*Nz - Lz
    rmag = np.sqrt(Rx*Rx + Ry*Ry + Rz*Rz)
    rmag = np.where(rmag < 1e-9, 1.0, rmag)
    Rx = Rx / rmag; Ry = Ry / rmag; Rz = Rz / rmag

    # r·v
    rdotv = Rx*Vx + Ry*Vy + Rz*Vz
    rdotv = np.maximum(rdotv, 0.0)

    # lighting params
    Iamb = np.array(lighting["Iamb"], dtype=float)
    Il = np.array(lighting["Il"], dtype=float)
    Ka = float(lighting["Ka"])
    Ks = float(lighting["Ks"])
    eta = float(lighting["eta"])
    Kd = np.array(lighting["Kd"], dtype=float)
    Od = np.array(lighting["Od"], dtype=float)

    # compute channels
    # shape gets broadcast
    Ia_r = Iamb[0] * Ka * Od[0]
    Ia_g = Iamb[1] * Ka * Od[1]
    Ia_b = Iamb[2] * Ka * Od[2]

    Id_r = Il[0] * Kd[0] * Od[0] * ndotl
    Id_g = Il[1] * Kd[1] * Od[1] * ndotl
    Id_b = Il[2] * Kd[2] * Od[2] * ndotl

    Is_r = Il[0] * Ks * (rdotv ** eta)
    Is_g = Il[1] * Ks * (rdotv ** eta)
    Is_b = Il[2] * Ks * (rdotv ** eta)

    Rchan = Ia_r + Id_r + Is_r
    Gchan = Ia_g + Id_g + Is_g
    Bchan = Ia_b + Id_b + Is_b

    # clamp and convert
    out = np.stack([Rchan, Gchan, Bchan], axis=-1)
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out  # shape (...,3)

def rasterize_mesh(triangles, proj_results, width, height, vertices_world=None, basis=None, lighting=None, ssaa=1):
    """
    triangles: list of (a,b,c) indices
    proj_results: list of dicts per vertex { 'view':(Xv,Yv,Zv), 'pixel':(px,py), 'visible':bool, ... }
    width,height: target framebuffer dimensions (render size, may be scaled for SSAA)
    ssaa: supersampling factor (1 means no SSAA; if >1, we render at higher resolution and downsample)
    Returns: framebuffer as numpy array shape (height, width, 3) dtype uint8 and tri_pixel sets (for outlines)
    """
    # We'll render into numpy arrays for speed
    H = height
    W = width
    framebuffer = np.zeros((H, W, 3), dtype=np.uint8)
    zbuf = np.full((H, W), np.inf, dtype=np.float32)

    # prepare per-vertex arrays
    n_vertices = len(proj_results)
    pix_x = np.empty(n_vertices, dtype=float)
    pix_y = np.empty(n_vertices, dtype=float)
    vis = np.zeros(n_vertices, dtype=bool)
    viewX = np.empty(n_vertices, dtype=float)
    viewY = np.empty(n_vertices, dtype=float)
    viewZ = np.empty(n_vertices, dtype=float)

    for i, v in enumerate(proj_results):
        px, py = v.get("pixel", (None,None))
        if px is None:
            pix_x[i] = np.nan; pix_y[i] = np.nan; vis[i] = False
        else:
            pix_x[i] = float(px)
            pix_y[i] = float(py)
            vis[i] = bool(v.get("visible", False))
        vv = v.get("view", (0.0,0.0,0.0))
        viewX[i] = vv[0]; viewY[i] = vv[1]; viewZ[i] = vv[2]

    # compute per-vertex normals (in view coords)
    if vertices_world is not None and basis is not None:
        vnorms_world = compute_vertex_normals_world(vertices_world, triangles)
        vnorms_view = []
        for n in vnorms_world:
            nv = transform.world_to_view_vector(n, basis)
            mag = math.sqrt(nv[0]*nv[0] + nv[1]*nv[1] + nv[2]*nv[2])
            if mag < 1e-9:
                vnorms_view.append((0.0,0.0,1.0))
            else:
                vnorms_view.append((nv[0]/mag, nv[1]/mag, nv[2]/mag))
        vnorms_view = np.array(vnorms_view, dtype=float)
    else:
        vnorms_view = np.zeros((n_vertices,3), dtype=float)
        vnorms_view[:,2] = 1.0

    # Precompute lighting Pl in view coords
    if lighting is not None and basis is not None:
        pl_view = transform.world_to_view_point(lighting.get("Pl",(0.0,0.0,10.0)), basis)
    else:
        pl_view = (0.0,0.0,10.0)

    tri_pixels_map = {}

    # Iterate triangles
    for ti, (a,b,c) in enumerate(triangles):
        # index checks
        if a<0 or b<0 or c<0 or a>=n_vertices or b>=n_vertices or c>=n_vertices:
            tri_pixels_map[ti] = set()
            continue

        # quick visibility: all three vertices must be visible (consistent with earlier approach)
        if not (vis[a] and vis[b] and vis[c]):
            tri_pixels_map[ti] = set()
            continue

        x1 = pix_x[a]; y1 = pix_y[a]
        x2 = pix_x[b]; y2 = pix_y[b]
        x3 = pix_x[c]; y3 = pix_y[c]

        # screen-space area test
        area2 = (x2-x1)*(y3-y1) - (y2-y1)*(x3-x1)
        if abs(area2) < 1e-3:
            tri_pixels_map[ti] = set(); continue

        # bounding box
        minx = int(max(math.floor(min(x1,x2,x3)), 0))
        maxx = int(min(math.ceil(max(x1,x2,x3)), W-1))
        miny = int(max(math.floor(min(y1,y2,y3)), 0))
        maxy = int(min(math.ceil(max(y1,y2,y3)), H-1))
        if minx > maxx or miny > maxy:
            tri_pixels_map[ti] = set(); continue

        # build grid for bbox (vectorized)
        xs = np.arange(minx, maxx+1, dtype=float)
        ys = np.arange(miny, maxy+1, dtype=float)
        Xg, Yg = np.meshgrid(xs, ys)  # shape (h,w)

        # compute barycentric using area method (vectorized)
        denom = ( (y2 - y3)*(x1 - x3) + (x3 - x2)*(y1 - y3) )
        # avoid denom==0 already checked by area2
        w1 = ( (y2 - y3)*(Xg - x3) + (x3 - x2)*(Yg - y3) ) / denom
        w2 = ( (y3 - y1)*(Xg - x3) + (x1 - x3)*(Yg - y3) ) / denom
        w3 = 1.0 - w1 - w2

        # mask inside triangle (allow tiny negative tolerance)
        inside = (w1 >= -1e-6) & (w2 >= -1e-6) & (w3 >= -1e-6)
        if not np.any(inside):
            tri_pixels_map[ti] = set(); continue

        # per-vertex invz and attributes for perspective-correct interpolation
        Z1 = viewZ[a]; Z2 = viewZ[b]; Z3 = viewZ[c]
        if Z1 == 0 or Z2 == 0 or Z3 == 0:
            tri_pixels_map[ti] = set(); continue
        invz1 = 1.0 / Z1; invz2 = 1.0 / Z2; invz3 = 1.0 / Z3

        X1_oz = viewX[a] * invz1; Y1_oz = viewY[a] * invz1
        X2_oz = viewX[b] * invz2; Y2_oz = viewY[b] * invz2
        X3_oz = viewX[c] * invz3; Y3_oz = viewY[c] * invz3

        # normals * invz
        na = vnorms_view[a]; nb = vnorms_view[b]; nc = vnorms_view[c]
        na_oz = na * invz1; nb_oz = nb * invz2; nc_oz = nc * invz3

        # compute invz interpolated
        invz = w1*invz1 + w2*invz2 + w3*invz3
        # avoid division by tiny numbers
        mask_valid = inside & np.isfinite(invz) & (invz > 1e-8)
        if not np.any(mask_valid):
            tri_pixels_map[ti] = set(); continue

        Zv = 1.0 / invz

        # Depth test: compare Zv with zbuf on the bbox
        z_sub = zbuf[miny:maxy+1, minx:maxx+1]
        Zv_masked = Zv
        # mask where new depth is nearer (smaller Zv)
        nearer = (Zv_masked < z_sub)
        write_mask = mask_valid & nearer
        if not np.any(write_mask):
            tri_pixels_map[ti] = set(); continue

        # compute P_view components
        X_oz = w1*X1_oz + w2*X2_oz + w3*X3_oz
        Y_oz = w1*Y1_oz + w2*Y2_oz + w3*Y3_oz
        # reconstruct view pos
        Xv = X_oz / invz
        Yv = Y_oz / invz
        Zv = Zv  # already

        # compute normal components
        Nox = w1*na_oz[0] + w2*nb_oz[0] + w3*nc_oz[0]
        Noy = w1*na_oz[1] + w2*nb_oz[1] + w3*nc_oz[1]
        Noz = w1*na_oz[2] + w2*nb_oz[2] + w3*nc_oz[2]

        Nx = Nox / invz
        Ny = Noy / invz
        Nz = Noz / invz

        # Determine which pixels will be written (boolean mask)
        wm = write_mask

        # Prepare flattened arrays for shading for only the pixels that pass
        # We'll index arrays with boolean mask
        Px = Xv[wm]
        Py = Yv[wm]
        Pz = Zv[wm]
        Nx_sel = Nx[wm]; Ny_sel = Ny[wm]; Nz_sel = Nz[wm]

        # compute colors vectorized
        color_pixels = phong_shade_vectorized(Px, Py, Pz, Nx_sel, Ny_sel, Nz_sel, pl_view, lighting)

        # Write to framebuffer and z-buffer
        # get linear indices into subregion
        ys_idx, xs_idx = np.nonzero(wm)
        # coords in full image:
        full_xs = xs_idx + minx
        full_ys = ys_idx + miny

        framebuffer[full_ys, full_xs, :] = color_pixels
        # update zbuf
        zbuf[full_ys, full_xs] = Pz

        # For tri_pixels_map (outline drawing), store integer pixel coordinates of inside region
        coords = set(zip([int(x) for x in full_xs.tolist()], [int(y) for y in full_ys.tolist()]))
        tri_pixels_map[ti] = coords

    return tri_pixels_map, framebuffer
