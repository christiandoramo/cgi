# display.py (atualizado: inclui render_help e mantém funções anteriores)
import pygame
from typing import Set, Tuple, List

Pixel = Tuple[int,int]
Color = Tuple[int,int,int]

def init_window(width: int, height: int, title: str = "Visualizador 3D (r - recarregar)") -> pygame.Surface:
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    screen.fill((0,0,0))
    pygame.display.flip()
    return screen

def clear_screen(surface: pygame.Surface, color: Color = (0,0,0)):
    surface.fill(color)

def draw_pixels(surface: pygame.Surface, pixels: Set[Pixel], color: Color = (255,255,255)):
    if not pixels:
        return
    surface.lock()
    try:
        w, h = surface.get_size()
        for (x,y) in pixels:
            if 0 <= x < w and 0 <= y < h:
                surface.set_at((x,y), color)
    finally:
        surface.unlock()

def present():
    pygame.display.flip()

def quit_pygame():
    pygame.quit()

# ----------------- Texto, lista e panel de ajuda -----------------

def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int,int],
              color: Color = (255,255,255), font_name: str = None, font_size: int = 18) -> pygame.Rect:
    font = pygame.font.SysFont(font_name, font_size)
    surf = font.render(text, True, color)
    rect = surf.get_rect(topleft=pos)
    surface.blit(surf, rect)
    return rect

def render_object_list_with_highlight(surface: pygame.Surface, items: List[str],
                       top_left: Tuple[int,int] = (8,8),
                       width: int = 200,
                       font_name: str = None,
                       font_size: int = 18,
                       bg_color: Color = (30,30,30),
                       item_color: Color = (220,220,220),
                       selected_color: Color = (255,200,0),
                       padding: int = 4,
                       selected_index: int = None) -> List[Tuple[int, pygame.Rect, str]]:
    x0, y0 = top_left
    font = pygame.font.SysFont(font_name, font_size)
    line_height = font.get_linesize() + padding
    total_h = line_height * len(items) + padding
    total_w = width
    bg_rect = pygame.Rect(x0-2, y0-2, total_w+4, total_h+4)
    s = pygame.Surface((bg_rect.w, bg_rect.h), flags=pygame.SRCALPHA)
    s.fill((*bg_color, 220))
    surface.blit(s, (bg_rect.x, bg_rect.y))

    rects = []
    for i, item in enumerate(items):
        iy = y0 + i * line_height
        if selected_index is not None and i == selected_index:
            item_bg = pygame.Rect(x0 + padding//2, iy + padding//2, total_w - padding, line_height - padding)
            pygame.draw.rect(surface, (40,40,80), item_bg)
        color = selected_color if (selected_index is not None and i == selected_index) else item_color
        txt_surf = font.render(item, True, color)
        txt_rect = txt_surf.get_rect(topleft=(x0 + padding, iy + padding//2))
        surface.blit(txt_surf, txt_rect)
        rects.append((i, txt_rect, item))
    return rects

def render_help(surface: pygame.Surface, lines: List[str],
                top_left: Tuple[int,int] = None,
                font_name: str = None,
                font_size: int = 16,
                bg_color: Tuple[int,int,int] = (10,10,10),
                text_color: Tuple[int,int,int] = (230,230,230),
                padding: int = 6):
    """
    Desenha uma caixa de ajuda com as linhas fornecidas.
    Se top_left for None, posiciona no canto inferior esquerdo.
    """
    font = pygame.font.SysFont(font_name, font_size)
    line_height = font.get_linesize()
    n = len(lines)
    surf_h = n * (line_height + 2) + padding*2
    surf_w = max(font.size(line)[0] for line in lines) + padding*2

    screen_w, screen_h = surface.get_size()
    if top_left is None:
        x0 = 8
        y0 = screen_h - surf_h - 8
    else:
        x0, y0 = top_left

    bg_surf = pygame.Surface((surf_w, surf_h), flags=pygame.SRCALPHA)
    # fundo semi-transparente
    bg_surf.fill((*bg_color, 200))
    # borda
    pygame.draw.rect(bg_surf, (80,80,80), bg_surf.get_rect(), 1)
    surface.blit(bg_surf, (x0, y0))

    # desenhar linhas
    for i, line in enumerate(lines):
        ty = y0 + padding + i * (line_height + 2)
        txt_surf = font.render(line, True, text_color)
        surface.blit(txt_surf, (x0 + padding, ty))
