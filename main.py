# main.py (atualizado: suporte a lista clicável de objetos em "formas/")
import os
import sys
import time
import glob

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

def find_formas_objects(folder: str = "formas"):
    """
    Retorna lista de nomes (sem .byu) encontrados na pasta 'formas' ordenados alfabeticamente.
    """
    if not os.path.isdir(folder):
        return []
    pattern = os.path.join(folder, "*.byu")
    files = glob.glob(pattern)
    names = [os.path.splitext(os.path.basename(p))[0] for p in files]
    names = sorted(names)
    return names

def load_mesh_for_name(name: str, folder: str = "formas"):
    """
    Constrói o caminho e carrega o .byu correspondente.
    Retorna (verts, tris) ou lança erro.
    """
    path = os.path.join(folder, name + ".byu")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Arquivo BYU não encontrado: {path}")
    verts, tris = byu_loader.load_byu(path)
    return verts, tris

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

def ask_filename():
    name = input("Digite o nome do arquivo .byu (sem a extensão), ex: 'triangulo' ou 'formas/triangulo': ").strip()
    if not name:
        print("Nome vazio. Cancelando.")
        sys.exit(0)
    filename = name + ".byu"
    if not os.path.isfile(filename) and not os.path.isfile(os.path.join("formas", filename)):
        print(f"Arquivo '{filename}' não encontrado no diretório atual nem em 'formas/'.")
        sys.exit(1)
    # prefer formas/<name>.byu if exists
    if os.path.isfile(os.path.join("formas", filename)):
        return os.path.join("formas", filename)
    return filename

def main():
    # descobrir objetos em formas/
    objects = find_formas_objects("formas")
    if objects:
        print("Objetos encontrados em 'formas/':", objects)
    else:
        print("Nenhum arquivo .byu encontrado em 'formas/' (continue com prompt manual).")

    # inicial load via prompt (mantive sua etapa inicial)
    filename = ask_filename()
    # se o usuário entrou 'formas/triangulo' eu mantenho o caminho direto; caso contrário, se entrou 'triangulo', 
    # o byu_loader aceita caminho relativo normal
    try:
        verts, tris = byu_loader.load_byu(filename)
        current_obj_name = os.path.splitext(os.path.basename(filename))[0]
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

    # inicializa janela
    try:
        screen = display.init_window(WIDTH, HEIGHT)
    except Exception as e:
        print("Erro ao inicializar janela gráfica (pygame).", e)
        sys.exit(1)

    # flags interativas
    show_outline = False
    show_vertices = False

    # primeira renderização
    all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
    outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)

    # desenha inicialmente e desenha a lista de objetos no topo (overlay)
    display.clear_screen(screen, (0,0,0))
    display.draw_pixels(screen, all_pixels, (255,255,255))
    if show_outline:
        display.draw_pixels(screen, outline_pixels, (255,0,0))
    if show_vertices:
        display.draw_pixels(screen, vertex_pixels, (0,255,0))

    # desenhar lista de objetos e guardar os rects retornados
    object_rects = []
    if objects:
        object_rects = display.render_object_list_with_highlight(screen, objects,
                                        top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                        font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name) if current_obj_name in objects else None))
    display.present()

    import pygame
    clock = pygame.time.Clock()
    running = True
    print("Janela aberta. Teclas: R=recarregar camera.txt | O=toggle contorno | V=toggle vértices | Z/X=zoom in/out | P=salvar screenshot | ESC=sair")
    print("Clique num nome na lista (canto superior esquerdo) para trocar o objeto.")

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # clique esquerdo: verificar se foi num item da lista
                mx, my = ev.pos
                clicked_index = None
                for (idx, rect, name) in object_rects:
                    if rect.collidepoint((mx, my)):
                        clicked_index = idx
                        clicked_name = name
                        break
                if clicked_index is not None:
                    # carregar o novo objeto clicado
                    try:
                        print(f"Clique detectado: carregar objeto '{clicked_name}'...")
                        verts, tris = load_mesh_for_name(clicked_name, folder="formas")
                        current_obj_name = clicked_name
                        # rebuild frame
                        all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                        outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                        # redesenhar tudo
                        display.clear_screen(screen, (0,0,0))
                        display.draw_pixels(screen, all_pixels, (255,255,255))
                        if show_outline:
                            display.draw_pixels(screen, outline_pixels, (255,0,0))
                        if show_vertices:
                            display.draw_pixels(screen, vertex_pixels, (0,255,0))
                        # redesenhar lista com destaque no item clicado
                        object_rects = display.render_object_list_with_highlight(screen, objects,
                                        top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                        font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name) if current_obj_name in objects else None))
                        display.present()
                    except Exception as e:
                        print("Falha ao carregar objeto clicado:", e)
                # caso clique fora da lista, nada acontece (preserva clicks normais)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_r:
                    # recarregar câmera
                    print("\nTecla 'R' detectada: recarregando camera.txt...")
                    cam = camera.load_camera(camfile)
                    camera.pretty_print_camera(cam)
                    # recomputar frame com os mesmos verts/tris
                    all_pixels, proj_results, tri_pixels_map = build_frame(verts, tris, cam, WIDTH, HEIGHT)
                    outline_pixels, vertex_pixels = make_outline_and_vertices(tris, proj_results, WIDTH, HEIGHT)
                    display.clear_screen(screen, (0,0,0))
                    display.draw_pixels(screen, all_pixels, (255,255,255))
                    if show_outline:
                        display.draw_pixels(screen, outline_pixels, (255,0,0))
                    if show_vertices:
                        display.draw_pixels(screen, vertex_pixels, (0,255,0))
                    # redesenhar lista (mesmo destaque)
                    object_rects = display.render_object_list_with_highlight(screen, objects,
                                        top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                        font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name) if current_obj_name in objects else None))
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
                    object_rects = display.render_object_list_with_highlight(screen, objects,
                                        top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                        font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name) if current_obj_name in objects else None))
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
                    object_rects = display.render_object_list_with_highlight(screen, objects,
                                        top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                        font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name) if current_obj_name in objects else None))
                    display.present()
                elif ev.key == pygame.K_z:
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
                    object_rects = display.render_object_list_with_highlight(screen, objects,
                                        top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                        font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name) if current_obj_name in objects else None))
                    display.present()
                elif ev.key == pygame.K_x:
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
                    object_rects = display.render_object_list_with_highlight(screen, objects,
                                        top_left=OBJ_LIST_TOPLEFT, width=OBJ_LIST_WIDTH,
                                        font_size=OBJ_FONT_SIZE, selected_index=(objects.index(current_obj_name) if current_obj_name in objects else None))
                    display.present()
                elif ev.key == pygame.K_p:
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
