"""
checkpoint.py
--------------
Punto de respawn a mitad de cada nivel. Importante: NO se dibuja como
bandera ni marcador genérico — Persona 3 debe representarlo con un sprite
que se sienta parte del mundo (una banca, una caja, una roca...). Aquí
solo está la lógica, el rectángulo de colisión y un placeholder de color.

Cuando el jugador lo toca por primera vez, queda "activado" y la escena
debe guardar su posición como el punto de reaparición vigente. Si el
jugador es derrotado después, PlayScene llama a player.respawn_at(...)
usando checkpoint.respawn_point.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.entity_base import Entity


class Checkpoint(Entity):
    def __init__(self, x: float, y: float, width: int = 16, height: int = 32) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.activated = False

    @property
    def respawn_point(self) -> tuple[float, float]:
        # Un poco arriba del rect para que el jugador no reaparezca metido en el suelo.
        return (self.rect.centerx - settings.PLAYER_WIDTH / 2, self.rect.top - settings.PLAYER_HEIGHT)

    def check(self, player_rect: pygame.Rect) -> bool:
        """
        Llamar cada frame desde PlayScene con el rect del jugador.
        Devuelve True solo en el frame exacto en que se activa por primera
        vez (para que Persona 3 dispare un sonido/efecto de "checkpoint").
        """
        if not self.activated and self.rect.colliderect(player_rect):
            self.activated = True
            return True
        return False

    def draw(self, surface: pygame.Surface, camera) -> None:
        color = settings.COLOR_CHECKPOINT_ON if self.activated else settings.COLOR_CHECKPOINT_OFF
        self.draw_placeholder(surface, camera, self.rect, color)
