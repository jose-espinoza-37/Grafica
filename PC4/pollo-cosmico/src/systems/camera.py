"""
camera.py
----------
Cámara simple de seguimiento: se centra en un objetivo (normalmente el
Player) con un poco de suavizado para que no se sienta brusca, y se puede
limitar para que no se salga de los bordes del nivel.
"""

from __future__ import annotations
import pygame

from src.core import settings


class Camera:
    def __init__(
        self,
        view_width: int = settings.BASE_WIDTH,
        view_height: int = settings.BASE_HEIGHT,
        level_width: int | None = None,
        level_height: int | None = None,
    ) -> None:
        self.view_width = view_width
        self.view_height = view_height
        self.level_width = level_width
        self.level_height = level_height
        self.x = 0.0
        self.y = 0.0

    def set_level_bounds(self, level_width: int, level_height: int) -> None:
        self.level_width = level_width
        self.level_height = level_height

    def update(self, dt: float, target_rect: pygame.Rect) -> None:
        target_x = target_rect.centerx - self.view_width / 2
        target_y = target_rect.centery - self.view_height / 2

        smooth = min(1.0, settings.CAMERA_SMOOTH * 60 * dt)  # normalizado a 60 fps
        self.x += (target_x - self.x) * smooth
        self.y += (target_y - self.y) * smooth

        if self.level_width is not None:
            self.x = max(0.0, min(self.x, max(0.0, self.level_width - self.view_width)))
        if self.level_height is not None:
            self.y = max(0.0, min(self.y, max(0.0, self.level_height - self.view_height)))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Convierte un rect de coordenadas del mundo a coordenadas de pantalla."""
        return rect.move(-round(self.x), -round(self.y))

    def apply_pos(self, x: float, y: float) -> tuple[int, int]:
        return round(x - self.x), round(y - self.y)
