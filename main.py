# main.py (inicia automaticamente, sem precisar digitar nome)
import os
import sys
import time
import glob
import math

import byu_loader
import camera
import transform
import projection
import rasterizer
import display

# resolução padrão
WIDTH = 800
HEIGHT = 600

# UI list settings
OBJ_LIST_TOPLEFT = (8, 8)
OBJ_LIST_WIDTH = 220
OBJ_FONT_SIZE = 18

# sensibilidade de rotação (radianos por pixel)
AZIMUTH_SENSITIVITY = 0.008  # horizontal
ELEVATION_SENSITIVITY = 0.006  # vertical
ELEVATION_MIN = -math.radians(89.0)
ELEVATION_MAX = math.radians(89.0)


def find_formas_objects(folder: str = "formas"):
    """Retorna lista ordenada de nomes de objetos .byu encontrados na pasta."""
    if not os.path.isdir(folder):
        print(f"Pasta '{folder}' não encontrada — criando...")
        os.makedirs(folder, exist_ok=True)
    pattern = os.path.join(folder, "*.byu")
    files = glob.glob(pattern)
    names = [os.path.splitext(os.path.basename(p))[0] for p in files]
    names = sorted(names)
    return names


def load_mesh_for_name(name: str, folder: str = "formas"):
    path = os.path.join(folder, name + ".byu")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Arquivo BYU não encontrado: {path}")
    verts, tris = byu_loader.load_byu(path)
    return verts, tris


def compute_centroid(vertices):
    if not vertices:
        return (0.0, 0.0, 0.0)
    sx = sy = sz = 0.0
    for (x, y, z) in vertices:
        sx += x
        sy += y
        sz += z
    n = len(vertices)
    return (sx / n, sy / n, sz / n)


def vec_sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vec_add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vec_scale(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def vec_length(a): return math.sqrt(a[0]**2 + a[1]**2 + a[2]**2)


def cartesian_from_spherical(r, az, el):
    x = r * math.cos(el) * math.sin(az)
    y = r * math.sin(el)
    z = r * math.cos(el) * math.cos(az)
    return (x, y, z)


def spherical_from_cartesian(v):
    x, y, z = v
    r = math.sqrt(x*x + y*y + z*z)
    if r == 0:
        return (0.0, 0.0, 0.0)
    az = math.atan2(x, z)
    el = math.asin(y / r)
    return (r, az, el)


def build_frame(verts, tris, cam, width, height):
    basis = transform.compute_camera_basis(cam)
    view_coords = transform.world_to_view_vertices(verts, basis)
    proj_results = projection.world_view_to_screen_list(view_coords, cam, width, height)
    tri_pixels_map = rasterizer.rasterize_mesh(tris, proj_results, width, height)
    all_pixels = set()
    for pset in tri_pixels_map.values():
        all_pixels.update(pset)
    print("\n== Debug pipeline (resumo) ==")
    print(f"Vértices: {len(verts)}  |  Triângulos: {len(tris)}")
    print(f"Pixels preenchidos (todos triângulos): {len(all_pixels)}")
    if all_pixels:
        sample = sorted(list(all_pixels))[:10]
        print(f"Amostra de pixels: {sample}")
    else:
        print("Nenhum pixel preenchido (fora do frustum?).")
    print("================================\n")
    return all_pixels, proj_results, tri_pixels_map


def make_outline_and_vertices(tris, proj_results, width, height):
    outline_pixels = set()
    vertex_pixels = set()
    for (a, b, c) in tris:
        if a >= len(proj_results) or b >= len(proj_results) or c >= len(proj_results):
            continue
        pa = proj_results[a]["pixel"]
        pb = proj_results[b]["pixel"]
        pc = proj_results[c]["pixel"]
        if pa[0] is None or pb[0] is None or pc[0] is None:
            continue
        outline_pixels.update(rasterizer.bresenham_line_pixels(pa[0], pa[1], pb[0], pb[1]))
        outline_pixels.update(rasterizer.bresenham_line_pixels(pb[0], pb[1], pc[0], pc[1]))
        outline_pixels.update(rasterizer.bresenham_line_pixels(pc[0], pc[1], pa[0], pa[1]))
        for (vx, vy) in (pa, pb, pc):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    x = int(vx)+dx
                    y = int(vy)+dy
                    if 0 <= x < width and 0 <= y < height:
                        vertex_pixels.add((x, y))
    return outline_pixels, vertex_pixels


def main():
    # 1️⃣ buscar objetos
    objects = find_formas_objects("formas")
    if not objects:
        print("⚠️ Nenhum arquivo .byu encontrado na pasta 'formas/'.")
        print("Crie pelo menos um arquivo e reinicie o programa.")
        sys.exit(1)

    # 2️⃣ carregar o primeiro objeto
    current_obj_name = objects[0]
    print(f"Carregando objeto inicial: {current_obj_name}")
    verts, tris = load_mesh_for_name(current_obj_name)
    centroid = compute_centroid(verts)

    # 3️⃣ carregar câmera
    camfile = "camera.txt"
    cam = camera.load_camera(camfile)
    camera.pretty_print_camera(cam)

    # converter posição atual para esférico
    v_cent_cam = vec_sub(tuple(cam['C']), centroid)
    r, az, el = spherical_from_cartesian(v_cent_cam)

    # 4️⃣ inicializar janela
    try:
        screen = display.init_window(WIDTH, HEIGHT)
    except Exception as e:
        print("Erro ao inicializar pygame:", e)
        sys.exit(1)

    show_outline = False
    show_vertices = False

    # 5️⃣ construir e desenhar frame
    all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
    outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
    display.clear_screen(screen, (0, 0, 0))
    display.draw_pixels(screen, all_pixels, (255, 255, 255))
    object_rects = display.render_object_list_with_highlight(
        screen, objects, top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
        font_size=OBJ_FONT_SIZE, selected_index=0
    )

    help_lines = [
        "Comandos:",
        "R - recarregar camera.txt",
        "O - toggle contorno",
        "V - toggle vértices",
        "Z/X - zoom in/out",
        "P - salvar screenshot",
        "Clique (esq) nome na lista - trocar objeto",
        "Segure botão direito - orbitar câmera",
        "ESC - sair"
    ]
    display.render_help(screen, help_lines)
    display.present()

    import pygame
    clock = pygame.time.Clock()
    running = True
    rotating = False
    last_mouse = (0, 0)

    print("✅ Sistema iniciado. Use o mouse e teclas conforme instruções na tela.")

    # 6️⃣ loop principal
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:  # clique esquerdo = troca objeto
                    mx, my = ev.pos
                    for (idx, rect, name) in object_rects:
                        if rect.collidepoint((mx, my)):
                            print(f"🟢 Carregando '{name}'...")
                            verts, tris = load_mesh_for_name(name)
                            current_obj_name = name
                            centroid = compute_centroid(verts)
                            v_cent_cam = vec_sub(tuple(cam['C']), centroid)
                            r, az, el = spherical_from_cartesian(v_cent_cam)
                            all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                            outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                            display.clear_screen(screen, (0, 0, 0))
                            display.draw_pixels(screen, all_pixels, (255, 255, 255))
                            object_rects = display.render_object_list_with_highlight(
                                screen, objects, top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name))
                            )
                            display.render_help(screen, help_lines)
                            display.present()
                            break
                elif ev.button == 3:
                    rotating = True
                    last_mouse = ev.pos

            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button == 3:
                    rotating = False

            elif ev.type == pygame.MOUSEMOTION and rotating:
                mx, my = ev.pos
                lx, ly = last_mouse
                dx, dy = mx - lx, my - ly
                last_mouse = (mx, my)
                az += dx * AZIMUTH_SENSITIVITY
                el += -dy * ELEVATION_SENSITIVITY
                el = max(ELEVATION_MIN, min(ELEVATION_MAX, el))
                Crel = cartesian_from_spherical(r, az, el)
                Cnew = vec_add(centroid, Crel)
                cam['C'] = Cnew
                cam['N'] = vec_sub(centroid, Cnew)
                if 'V' not in cam:
                    cam['V'] = (0, 1, 0)
                all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                display.clear_screen(screen, (0, 0, 0))
                display.draw_pixels(screen, all_pixels, (255, 255, 255))
                object_rects = display.render_object_list_with_highlight(
                    screen, objects, top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                    font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name))
                )
                display.render_help(screen, help_lines)
                display.present()

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_r:
                    cam = camera.load_camera(camfile)
                    v_cent_cam = vec_sub(tuple(cam['C']), centroid)
                    r, az, el = spherical_from_cartesian(v_cent_cam)
                elif ev.key == pygame.K_o:
                    show_outline = not show_outline
                    print("Outline:", show_outline)
                elif ev.key == pygame.K_v:
                    show_vertices = not show_vertices
                    print("Vértices:", show_vertices)
                elif ev.key == pygame.K_z:
                    cam['d'] = float(cam.get('d', 1.0)) * 1.25
                elif ev.key == pygame.K_x:
                    cam['d'] = float(cam.get('d', 1.0)) / 1.25
                elif ev.key == pygame.K_p:
                    fname = f"screenshot_{int(time.time())}.png"
                    import pygame
                    pygame.image.save(screen, fname)
                    print(f"💾 Screenshot salvo: {fname}")

                # redesenha sempre após qualquer tecla
                all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                display.clear_screen(screen, (0, 0, 0))
                display.draw_pixels(screen, all_pixels, (255, 255, 255))
                if show_outline:
                    display.draw_pixels(screen, outline_pixels, (255, 0, 0))
                if show_vertices:
                    display.draw_pixels(screen, vertex_pixels, (0, 255, 0))
                object_rects = display.render_object_list_with_highlight(
                    screen, objects, top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                    font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name))
                )
                display.render_help(screen, help_lines)
                display.present()

        clock.tick(60)

    display.quit_pygame()
    print("Aplicação finalizada.")


if __name__ == "__main__":
    main()