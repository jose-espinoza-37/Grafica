"""
pixelate.py
------------
Todo el juego se dibuja sobre una superficie pequeña (settings.BASE_WIDTH x
settings.BASE_HEIGHT) y luego esa superficie se escala hacia la ventana real
SIN suavizado (pygame.transform.scale, no smoothscale), que es lo que da el
look de pixel art consistente sin importar la resolución de la ventana.
"""

from __future__ import annotations
import pygame

from src.core import settings


def make_render_surface() -> pygame.Surface:
    return pygame.Surface((settings.BASE_WIDTH, settings.BASE_HEIGHT))


def present(render_surface: pygame.Surface, window_surface: pygame.Surface) -> None:
    window_w, window_h = window_surface.get_size()

    scale = min(window_w / settings.BASE_WIDTH, window_h / settings.BASE_HEIGHT)
    scaled_w = max(1, int(settings.BASE_WIDTH * scale))
    scaled_h = max(1, int(settings.BASE_HEIGHT * scale))

    scaled = pygame.transform.scale(render_surface, (scaled_w, scaled_h))

    # Letterbox: centra la imagen escalada si la proporción no es exacta,
    # en vez de deformar el pixel art para llenar toda la ventana.
    window_surface.fill(settings.COLOR_BLACK)
    offset_x = (window_w - scaled_w) // 2
    offset_y = (window_h - scaled_h) // 2
    window_surface.blit(scaled, (offset_x, offset_y))
