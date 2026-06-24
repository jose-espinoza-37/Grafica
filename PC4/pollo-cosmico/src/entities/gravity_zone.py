"""
gravity_zone.py
-----------------
Zona rectangular donde la gravedad se comporta distinto - Nivel 2: Ciudad
Evacuada ("sectores con gravedad alterada"). No reemplaza la gravedad
global, solo la multiplica mientras el jugador está dentro de la zona.

gravity_scale:
    1.0  -> gravedad normal (fuera de cualquier zona)
    0.3  -> gravedad débil (cae lento, salta más alto/lejos)
    -1.0 -> gravedad invertida (cae "hacia arriba")

PlayScene debe revisar, cada frame, si player.rect choca con alguna zona
y pasarle ese gravity_scale a player.update(...). Si no choca con
ninguna, se usa 1.0 (gravedad normal).
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.entity_base import Entity


class GravityZone(Entity):
    def __init__(self, x: float, y: float, width: int, height: int, gravity_scale: float = 1.0) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.gravity_scale = gravity_scale

    def contains(self, other_rect: pygame.Rect) -> bool:
        return self.rect.colliderect(other_rect)

    def draw(self, surface: pygame.Surface, camera) -> None:
        self.draw_placeholder(surface, camera, self.rect, settings.COLOR_GRAVITY_ZONE)


def get_gravity_scale(player_rect: pygame.Rect, zones: list[GravityZone]) -> float:
    """Atajo para PlayScene: revisa todas las zonas y devuelve el primer
    gravity_scale que aplique, o 1.0 (normal) si no está en ninguna."""
    for zone in zones:
        if zone.contains(player_rect):
            return zone.gravity_scale
    return 1.0
