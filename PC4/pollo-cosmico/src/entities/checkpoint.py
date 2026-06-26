"""
checkpoint.py
--------------
Punto de respawn a mitad de cada nivel. Diseño diegético: una pila de
cajas con una linterna. La linterna está apagada (frame 0) hasta que el
jugador lo activa; después pulsa suavemente en loop (frames 1-3).

Cuando el jugador lo toca por primera vez, queda "activado" y PlayScene
usa checkpoint.respawn_point como punto de reaparición si el jugador cae.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.entity_base import Entity

_ANIM_FPS = 4.0   # velocidad del pulso (frames por segundo cuando está activo)


class Checkpoint(Entity):
    def __init__(self, x: float, y: float, width: int = 16, height: int = 32) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.activated = False
        self._anim_timer = 0.0
        self._anim_frame = 0   # 0 = apagado, 1-3 = ciclo de pulso

    @property
    def respawn_point(self) -> tuple[float, float]:
        return (self.rect.centerx - settings.PLAYER_WIDTH / 2, self.rect.top - settings.PLAYER_HEIGHT)

    def update(self, dt: float, player_rect: pygame.Rect) -> bool:
        """
        Llamar cada frame desde PlayScene. Actualiza activación y animación.
        Devuelve True solo en el frame exacto en que se activa (para sonido/efecto).
        """
        activated_now = False
        if not self.activated and self.rect.colliderect(player_rect):
            self.activated = True
            self._anim_frame = 1
            activated_now = True

        if not self.activated:
            self._anim_frame = 0
            self._anim_timer = 0.0
        else:
            self._anim_timer += dt
            interval = 1.0 / _ANIM_FPS
            if self._anim_timer >= interval:
                self._anim_timer -= interval
                # cicla frames 1 -> 2 -> 3 -> 1 -> ...
                self._anim_frame = (self._anim_frame % 3) + 1

        return activated_now

    def draw(self, surface: pygame.Surface, camera, assets=None) -> None:
        rect = camera.apply(self.rect)
        if assets is not None:
            frame = assets.get_player_frame('checkpoint', self._anim_frame, (rect.width, rect.height))
            surface.blit(frame, rect)
        else:
            color = settings.COLOR_CHECKPOINT_ON if self.activated else settings.COLOR_CHECKPOINT_OFF
            self.draw_placeholder(surface, camera, self.rect, color)
