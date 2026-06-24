"""
cyclic_platform.py
---------------------
Plataforma que aparece y desaparece en ciclos fijos. Representa
visualmente la "distorsión temporal" de la mitad de playa del Nivel 3,
sin necesitar ningún código real de manipulación del tiempo.

Mientras está visible, PlayScene debe incluir platform.solid_rect en la
lista de sólidos que se le pasa a collision.move_and_collide(...). Mientras
está invisible, solid_rect devuelve None y simplemente no se incluye.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.entity_base import Entity
from src.entities.cyclic_timer import CyclicTimer


class CyclicPlatform(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        visible_time: float = 2.0,
        hidden_time: float = 1.5,
        start_visible: bool = True,
    ) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.timer = CyclicTimer(visible_time, hidden_time, start_visible)

    def update(self, dt: float) -> None:
        self.timer.update(dt)

    @property
    def solid_rect(self) -> pygame.Rect | None:
        return self.rect if self.timer.visible else None

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.timer.visible:
            self.draw_placeholder(surface, camera, self.rect, settings.COLOR_CYCLIC_PLATFORM)
