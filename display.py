# display.py
import pygame
from typing import Set, Tuple

Pixel = Tuple[int,int]
Color = Tuple[int,int,int]

def init_window(width: int, height: int, title: str = "Visualizador 3D (r - recarregar)") -> pygame.Surface:
    """
    Inicializa pygame, cria janela e retorna a surface principal.
    """
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    screen.fill((0,0,0))
    pygame.display.flip()
    return screen

def clear_screen(surface: pygame.Surface, color: Color = (0,0,0)):
    """
    Limpa a surface inteira com a cor (preto por padrão).
    """
    surface.fill(color)

def draw_pixels(surface: pygame.Surface, pixels: Set[Pixel], color: Color = (255,255,255)):
    """
    Desenha cada pixel da coleção 'pixels' (conjunto de tuplas (x,y)) na surface com a cor dada.
    Usa lock/unlock para performance e segurança.
    """
    if not pixels:
        return
    surface.lock()
    try:
        w, h = surface.get_size()
        clamped = 0
        for (x,y) in pixels:
            if 0 <= x < w and 0 <= y < h:
                surface.set_at((x,y), color)
            else:
                clamped += 1
    finally:
        surface.unlock()

def present():
    """
    Atualiza o display (flip).
    """
    pygame.display.flip()

def quit_pygame():
    pygame.quit()