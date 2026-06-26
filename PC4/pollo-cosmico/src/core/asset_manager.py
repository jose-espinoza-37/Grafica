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

# Sprite sheets del jugador: key -> (ruta, columnas, filas)
# La fila 0 es la animación de caminar (la única que se usa actualmente).
# chiken.png está en 4×2 hasta que se regenere como 4×3.
_PLAYER_SHEETS: dict[str, tuple[str, int, int]] = {
    # Jugador
    'player_human':  ('assets/sprites/player/humano/humano_strip.png',              7, 1),
    'player_patas':  ('assets/sprites/player/patas_pollo/patas_strip.png',          7, 1),
    'player_alas':   ('assets/sprites/player/alas_pollo/alas_strip.png',            7, 1),
    'player_pollo':  ('assets/sprites/player/pollo_completo/pollo_strip.png',       4, 1),
    # Checkpoint (frame 0=apagado, frames 1-3=pulso activo)
    'checkpoint':    ('assets/sprites/checkpoint/checkpoint_strip.png',             4, 1),
    # Power-ups
    'pluma_cosmica': ('assets/sprites/powerups/pluma_cosmica/pluma_strip.png',      4, 1),
    'disfraz_pio':   ('assets/sprites/powerups/disfraz_pio/disfraz_strip.png',      4, 1),
    # Enemigos
    'robot':         ('assets/sprites/enemies/robot/robot_strip.png',               6, 1),
    'mutante':       ('assets/sprites/enemies/mutante/mutante_strip.png',           6, 1),
}


def _remove_magenta_bg(surf: pygame.Surface) -> pygame.Surface:
    """Elimina el fondo magenta (#FF00FF) de un PNG con transparencia."""
    try:
        import pygame.surfarray as psa
        import numpy as np
        surf = surf.convert_alpha()
        pixels = psa.pixels3d(surf)
        alpha  = psa.pixels_alpha(surf)
        r = pixels[:, :, 0].astype(np.int16)
        g = pixels[:, :, 1].astype(np.int16)
        b = pixels[:, :, 2].astype(np.int16)
        mask = (r - g > 50) & (b - g > 50) & (r > 100)
        alpha[mask] = 0
        del pixels, alpha
        return surf
    except Exception:
        # Sin numpy: convert() (sin alpha por pixel) + colorkey.
        # NOTA: convert_alpha() ignora el colorkey, por eso usamos convert().
        s = surf.convert()
        s.set_colorkey((255, 0, 255))
        return s


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

    # ------------------------------------------------------------------
    # Sprite sheets del jugador
    # ------------------------------------------------------------------
    def get_player_frame(
        self,
        key: str,
        col: int,
        size: tuple[int, int],
        flip_x: bool = False,
    ) -> pygame.Surface:
        """
        Devuelve un fotograma de la fila 0 del sprite sheet del jugador,
        escalado a 'size'. El resultado se cachea; crear un flip da otra
        entrada en caché (es barato a 14×20 px).
        """
        cache_key = f"__pf__{key}_{col}_{size}_{flip_x}"
        if cache_key in self._images:
            return self._images[cache_key]

        frame = self._extract_player_frame(key, col, size)
        if flip_x:
            frame = pygame.transform.flip(frame, True, False)
        self._images[cache_key] = frame
        return frame

    def _extract_player_frame(
        self, key: str, col: int, size: tuple[int, int]
    ) -> pygame.Surface:
        sheet_key = f"__sheet__{key}"
        if sheet_key not in self._images:
            if key not in _PLAYER_SHEETS:
                return self._placeholder(size)
            path, cols, rows = _PLAYER_SHEETS[key]
            if not os.path.isfile(path):
                return self._placeholder(size)
            raw = pygame.image.load(path).convert_alpha()
            raw = _remove_magenta_bg(raw)
            self._images[sheet_key] = (raw, cols, rows)

        raw, cols, rows = self._images[sheet_key]
        fw = raw.get_width() // cols
        fh = raw.get_height() // rows
        col = col % cols
        frame = raw.subsurface(pygame.Rect(col * fw, 0, fw, fh)).copy()
        scaled = pygame.transform.scale(frame, size)
        # pygame.transform.scale no preserva el colorkey; hay que re-aplicarlo.
        ck = raw.get_colorkey()
        if ck is not None:
            scaled.set_colorkey(ck)
        return scaled
