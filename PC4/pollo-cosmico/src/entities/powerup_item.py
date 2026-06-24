"""
powerup_item.py
------------------
Ítem recogible que aparece en el nivel. Al tocarlo, el jugador obtiene el
power-up correspondiente (ver systems/powerup_system.py). Pueden colocarse
varias veces repetidas dentro de un mismo nivel - no son de un solo uso
por nivel, cada instancia es independiente.

Recordar: KIND_DISGUISE solo debe colocarse desde el Nivel 2 en adelante,
nunca en el Nivel 1 (los robots no son mutantes, el disfraz no tendría
sentido ahí). Eso lo decide quien diseñe el nivel, este archivo no lo
restringe por código a propósito, para no atarse de manos si el diseño
cambia más adelante.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.entity_base import Entity


class PowerUpItem(Entity):
    KIND_DOUBLE_JUMP = "double_jump"   # Pluma Cósmica
    KIND_DISGUISE = "disguise"          # Yo También Digo Pío

    def __init__(self, x: float, y: float, kind: str, width: int = 12, height: int = 12) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.kind = kind
        self.collected = False

    def try_collect(self, player) -> bool:
        if self.collected or not self.rect.colliderect(player.rect):
            return False

        if self.kind == self.KIND_DOUBLE_JUMP:
            player.powerups.pickup_double_jump()
        elif self.kind == self.KIND_DISGUISE:
            player.powerups.pickup_disguise()

        self.collected = True
        self.alive = False
        return True

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.collected:
            return
        color = (
            settings.COLOR_POWERUP_DOUBLE_JUMP
            if self.kind == self.KIND_DOUBLE_JUMP
            else settings.COLOR_POWERUP_DISGUISE
        )
        self.draw_placeholder(surface, camera, self.rect, color)
