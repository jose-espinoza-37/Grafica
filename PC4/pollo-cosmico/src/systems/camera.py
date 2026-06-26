"""
camera.py
----------
Cámara simple de seguimiento con suavizado y límites de nivel.

Novedad respecto a la versión anterior:
  - y_offset (por defecto +32 px): desplaza el punto de enfoque HACIA ABAJO,
    de modo que la cámara muestre más suelo y menos cielo vacío.
    Con offset=0 el jugador queda exactamente centrado en pantalla.
    Con offset=+32 el jugador aparece un poco por encima del centro,
    dejando más espacio visual debajo (donde ocurre la acción).
    Ajusta Y_FOCUS_OFFSET en settings.py si quieres otro valor.
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
        self.view_width  = view_width
        self.view_height = view_height
        self.level_width  = level_width
        self.level_height = level_height
        self.x = 0.0
        self.y = 0.0

    def set_level_bounds(self, level_width: int, level_height: int) -> None:
        self.level_width  = level_width
        self.level_height = level_height

    def update(self, dt: float, target_rect: pygame.Rect) -> None:
        # Offset vertical: positivo = el jugador aparece más arriba en pantalla
        # (la cámara mira más hacia el suelo).
        y_offset = getattr(settings, "CAMERA_Y_OFFSET", 32)

        target_x = target_rect.centerx - self.view_width  / 2
        target_y = target_rect.centery - self.view_height / 2 + y_offset

        smooth = min(1.0, settings.CAMERA_SMOOTH * 60 * dt)
        self.x += (target_x - self.x) * smooth
        self.y += (target_y - self.y) * smooth

        if self.level_width is not None:
            self.x = max(0.0, min(self.x, max(0.0, self.level_width  - self.view_width)))
        if self.level_height is not None:
            self.y = max(0.0, min(self.y, max(0.0, self.level_height - self.view_height)))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-round(self.x), -round(self.y))

    def apply_pos(self, x: float, y: float) -> tuple[int, int]:
        return round(x - self.x), round(y - self.y)