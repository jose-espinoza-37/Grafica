"""
entity_base.py
---------------
Clase base mínima para cualquier objeto de gameplay (Player, Enemy,
Checkpoint, power-ups, plataformas cíclicas...). No obliga a heredar de
PhysicsBody porque no todas las entidades necesitan gravedad (un
Checkpoint es estático, por ejemplo).

Solo da una interfaz común (update/draw) y un helper para dibujar un
rectángulo de color como placeholder mientras no haya sprite final.
"""

from __future__ import annotations
import pygame


class Entity:
    def __init__(self) -> None:
        self.alive = True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera) -> None:
        pass

    @staticmethod
    def draw_placeholder(surface: pygame.Surface, camera, rect: pygame.Rect, color) -> None:
        pygame.draw.rect(surface, color, camera.apply(rect))
