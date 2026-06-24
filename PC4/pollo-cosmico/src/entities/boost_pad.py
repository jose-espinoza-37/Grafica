"""
boost_pad.py
-------------
Representa las raíces/plantas que "empujan hacia arriba" al jugador en la
mitad de bosque del Nivel 3 - saltos más altos sin necesitar física nueva,
solo un impulso vertical fijo al pisar la zona.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.entity_base import Entity


class BoostPad(Entity):
    def __init__(self, x: float, y: float, width: int, height: int, boost_velocity: float | None = None) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.boost_velocity = boost_velocity if boost_velocity is not None else settings.BOOST_PAD_VELOCITY

    def try_boost(self, player) -> bool:
        """Llamar desde PlayScene cada frame. Solo impulsa si el jugador
        está cayendo o quieto sobre ella (vy >= 0), no si ya está subiendo."""
        if player.rect.colliderect(self.rect) and player.vy >= 0:
            player.vy = self.boost_velocity
            player.on_ground = False
            return True
        return False

    def draw(self, surface: pygame.Surface, camera) -> None:
        self.draw_placeholder(surface, camera, self.rect, settings.COLOR_BOOST_PAD)
