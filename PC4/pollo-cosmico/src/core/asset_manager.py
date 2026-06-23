"""
asset_manager.py
-----------------
Carga y cachea imágenes y sonidos para que nunca se lea el mismo
archivo dos veces desde disco. Persona 2 y Persona 3 deben pedir
sus recursos siempre a través de esta clase (game.assets.get_image(...)),
nunca con pygame.image.load directamente en sus propios archivos.
"""

import os
import pygame


class AssetManager:
    def __init__(self):
        self._images: dict[str, pygame.Surface] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._fonts: dict[tuple[str, int], pygame.font.Font] = {}
        self._missing_image_cache: dict[tuple[int, int], pygame.Surface] = {}

    # ------------------------------------------------------------------
    # Imágenes
    # ------------------------------------------------------------------
    def get_image(self, path: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        """
        Devuelve una imagen cacheada. Si el archivo no existe todavía
        (porque el arte aún no está listo), devuelve un placeholder
        magenta con tamaño 'size' en vez de romper el juego.
        """
        key = path if size is None else f"{path}@{size}"
        if key in self._images:
            return self._images[key]

        if not os.path.isfile(path):
            surface = self._placeholder(size or (32, 32))
        else:
            surface = pygame.image.load(path).convert_alpha()
            if size is not None:
                surface = pygame.transform.scale(surface, size)

        self._images[key] = surface
        return surface

    def _placeholder(self, size: tuple[int, int]) -> pygame.Surface:
        if size in self._missing_image_cache:
            return self._missing_image_cache[size]
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((255, 0, 255, 180))
        pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 1)
        self._missing_image_cache[size] = surf
        return surf

    # ------------------------------------------------------------------
    # Sonidos
    # ------------------------------------------------------------------
    def get_sound(self, path: str) -> pygame.mixer.Sound | None:
        if path in self._sounds:
            return self._sounds[path]

        if not os.path.isfile(path):
            return None

        sound = pygame.mixer.Sound(path)
        self._sounds[path] = sound
        return sound

    # ------------------------------------------------------------------
    # Fuentes
    # ------------------------------------------------------------------
    def get_font(self, path: str | None, size: int) -> pygame.font.Font:
        key = (path or "__default__", size)
        if key in self._fonts:
            return self._fonts[key]

        if path and os.path.isfile(path):
            font = pygame.font.Font(path, size)
        else:
            font = pygame.font.SysFont("arial", size)

        self._fonts[key] = font
        return font

    # ------------------------------------------------------------------
    def preload_images(self, paths: list[str]) -> None:
        """Util para cargar varias imágenes de una sola vez al iniciar un nivel."""
        for p in paths:
            self.get_image(p)
