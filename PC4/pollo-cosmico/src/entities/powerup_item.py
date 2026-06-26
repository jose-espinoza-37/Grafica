"""
powerup_item.py
------------------
Ítem recogible que aparece en el nivel. Al tocarlo, el jugador obtiene el
power-up correspondiente. Anima en loop (4 frames) y flota suavemente
arriba/abajo usando una onda seno sobre el timer de animación.

KIND_DISGUISE solo debe colocarse desde el Nivel 2 en adelante.
"""

from __future__ import annotations
import math
import pygame

from src.core import settings
from src.entities.entity_base import Entity

_ANIM_FPS = 6.0        # ciclo de animación del sprite
_BOB_SPEED = 3.0       # velocidad de la onda de flotación (radianes/s)
_BOB_AMPLITUDE = 3     # píxeles de desplazamiento vertical (en coords de canvas)

_SPRITE_KEY = {
    "double_jump": "pluma_cosmica",
    "disguise":    "disfraz_pio",
}


class PowerUpItem(Entity):
    KIND_DOUBLE_JUMP = "double_jump"
    KIND_DISGUISE = "disguise"

    def __init__(self, x: float, y: float, kind: str, width: int = 12, height: int = 12) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.kind = kind
        self.collected = False
        self._anim_timer = 0.0
        self._anim_frame = 0

    def update(self, dt: float) -> None:
        if self.collected:
            return
        self._anim_timer += dt
        interval = 1.0 / _ANIM_FPS
        if self._anim_timer >= interval:
            self._anim_timer -= interval
            self._anim_frame = (self._anim_frame + 1) % 4

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

    def draw(self, surface: pygame.Surface, camera, assets=None) -> None:
        if self.collected:
            return

        rect = camera.apply(self.rect)

        # Flotación seno (usa el timer acumulado total para suavidad)
        bob = int(math.sin(self._anim_timer * _BOB_SPEED + self._anim_frame) * _BOB_AMPLITUDE)
        draw_rect = rect.move(0, bob)

        if assets is not None:
            key = _SPRITE_KEY.get(self.kind)
            if key:
                frame = assets.get_player_frame(key, self._anim_frame, (rect.width, rect.height))
                surface.blit(frame, draw_rect)
                return

        color = (
            settings.COLOR_POWERUP_DOUBLE_JUMP
            if self.kind == self.KIND_DOUBLE_JUMP
            else settings.COLOR_POWERUP_DISGUISE
        )
        self.draw_placeholder(surface, camera, self.rect, color)
