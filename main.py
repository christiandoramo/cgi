# main.py (final - Parte 7)
import os
import sys
import time

import byu_loader
import camera
import transform
import projection
import rasterizer
import display

# resolução padrão
WIDTH = 800
HEIGHT = 600

def ask_filename():
    name = input("Digite o nome do arquivo .byu (sem a extensão), ex: 'triangulo' ou 'formas/triangulo': ").strip()
    if not name:
        print("Nome vazio. Cancelando.")
        sys.exit(0)
    filename = name + ".byu"
    if not os.path.isfile(filename):
        print(f"Arquivo '{filename}' não encontrado no diretório atual ({os.getcwd()}).")
        sys.exit(1)
    return filename

def build_frame(verts, tris, cam, width, height):
    basis = transform.compute_camera_basis(cam)
    view_coords = transform.world_to_view_vertices(verts, basis)
    proj_results = projection.world_view_to_screen_list(view_coords, cam, width, height)
    tri_pixels_map = rasterizer.rasterize_mesh(tris, proj_results, width, height)
    all_pixels = set()
    for pset in tri_pixels_map.values():
        all_pixels.update(pset)
    # debug
    print("\n== Debug pipeline (resumo) ==")
    print(f"Vértices: {len(verts)}  |  Triângulos: {len(tris)}")
    print(f"Pixels preenchidos (todos triângulos): {len(all_pixels)}")
    if all_pixels:
        sample = sorted(list(all_pixels))[:10]
        print(f"Amostra de pixels: {sample}")
    else:
        print("Nenhum pixel preenchido (triângulos podem estar fora do frustum).")
    print("================================\n")
    return all_pixels, proj_results, tri_pixels_map

def make_outline_and_vertices(tris, proj_results, width, height):
    outline_pixels = set()
    vertex_pixels = set()
    for (a,b,c) in tris:
        if a >= len(proj_results) or b >= len(proj_results) or c >= len(proj_results): 
            continue
        pa = proj_results[a]["pixel"]; pb = proj_results[b]["pixel"]; pc = proj_results[c]["pixel"]
        if pa[0] is None or pb[0] is None or pc[0] is None:
            continue
        outline_pixels.update(rasterizer.bresenham_line_pixels(pa[0], pa[1], pb[0], pb[1]))
        outline_pixels.update(rasterizer.bresenham_line_pixels(pb[0], pb[1], pc[0], pc[1]))
        outline_pixels.update(rasterizer.bresenham_line_pixels(pc[0], pc[1], pa[0], pa[1]))
        for (vx, vy) in (pa, pb, pc):
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    x = int(vx)+dx; y = int(vy)+dy
                    if 0 <= x < width and 0 <= y < height:
                        vertex_pixels.add((x,y))
    return outline_pixels, vertex_pixels

def main():
    filename = ask_filename()
    try:
        verts, tris = byu_loader.load_byu(filename)
    except Exception as e:
        print("Erro ao carregar o arquivo .byu:", e)
        sys.exit(1)

    print("== Teste simples após carregar a malha ==")
    print(f"Vértices: {len(verts)}  |  Triângulos: {len(tris)}")
    for i, v in enumerate(verts[:5]):
        print(f"v[{i+1}] = {v}")
    for j, t in enumerate(tris[:5]):
        print(f"t[{j+1}] = ( {t[0]+1}, {t[1]+1}, {t[2]+1} )")

    camfile = "camera.txt"
    cam = camera.load_camera(camfile)
    camera.pretty_print_camera(cam)

    try:
        screen = display.init_window(WIDTH, HEIGHT)
    except Exception as e:
        print("Erro ao inicializar janela gráfica (pygame).", e)
        sys.exit(1)

    # flags interativas
    show_outline = False
    show_vertices = False

    all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
    outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)

    display.clear_screen(screen, (0,0,0))
    display.draw_pixels(screen, all_pixels, (255,255,255))
    if show_outline:
        display.draw_pixels(screen, outline_pixels, (255,0,0))
    if show_vertices:
        display.draw_pixels(screen, vertex_pixels, (0,255,0))
    display.present()

    import pygame
    clock = pygame.time.Clock()
    running = True
    print("Janela aberta. Teclas: R=recarregar camera.txt | O=toggle contorno | V=toggle vértices | Z/X=zoom in/out | P=salvar screenshot | ESC=sair")

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_r:
                    print("\nTecla 'R' detectada: recarregando camera.txt...")
                    cam = camera.load_camera(camfile)
                    camera.pretty_print_camera(cam)
                    all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                    outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                    display.clear_screen(screen, (0,0,0))
                    display.draw_pixels(screen, all_pixels, (255,255,255))
                    if show_outline:
                        display.draw_pixels(screen, outline_pixels, (255,0,0))
                    if show_vertices:
                        display.draw_pixels(screen, vertex_pixels, (0,255,0))
                    display.present()
                elif ev.key == pygame.K_o:
                    show_outline = not show_outline
                    print("Toggle contorno:", show_outline)
                    display.clear_screen(screen, (0,0,0))
                    display.draw_pixels(screen, all_pixels, (255,255,255))
                    if show_outline:
                        display.draw_pixels(screen, outline_pixels, (255,0,0))
                    if show_vertices:
                        display.draw_pixels(screen, vertex_pixels, (0,255,0))
                    display.present()
                elif ev.key == pygame.K_v:
                    show_vertices = not show_vertices
                    print("Toggle vértices:", show_vertices)
                    display.clear_screen(screen, (0,0,0))
                    display.draw_pixels(screen, all_pixels, (255,255,255))
                    if show_outline:
                        display.draw_pixels(screen, outline_pixels, (255,0,0))
                    if show_vertices:
                        display.draw_pixels(screen, vertex_pixels, (0,255,0))
                    display.present()
                elif ev.key == pygame.K_z:
                    # zoom in: aumentar d
                    cam['d'] = float(cam.get('d',1.0)) * 1.25
                    print(f"Zoom in (d = {cam['d']}) - reconstruindo frame")
                    all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                    outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                    display.clear_screen(screen, (0,0,0))
                    display.draw_pixels(screen, all_pixels, (255,255,255))
                    if show_outline:
                        display.draw_pixels(screen, outline_pixels, (255,0,0))
                    if show_vertices:
                        display.draw_pixels(screen, vertex_pixels, (0,255,0))
                    display.present()
                elif ev.key == pygame.K_x:
                    # zoom out: diminuir d
                    cam['d'] = float(cam.get('d',1.0)) / 1.25
                    print(f"Zoom out (d = {cam['d']}) - reconstruindo frame")
                    all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                    outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                    display.clear_screen(screen, (0,0,0))
                    display.draw_pixels(screen, all_pixels, (255,255,255))
                    if show_outline:
                        display.draw_pixels(screen, outline_pixels, (255,0,0))
                    if show_vertices:
                        display.draw_pixels(screen, vertex_pixels, (0,255,0))
                    display.present()
                elif ev.key == pygame.K_p:
                    # salvar screenshot
                    fname = f"screenshot_{int(time.time())}.png"
                    try:
                        pygame.image.save(screen, fname)
                        print(f"Screenshot salvo: {fname}")
                    except Exception as e:
                        print("Falha ao salvar screenshot:", e)

        clock.tick(60)

    display.quit_pygame()
    print("Aplicação finalizada.")

if __name__ == "__main__":
    main()