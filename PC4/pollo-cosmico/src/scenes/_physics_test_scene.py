"""
_physics_test_scene.py
------------------------
ESCENA TEMPORAL - solo para que Persona 1 pueda probar que física,
colisiones, cámara y pixelado funcionan bien (incluyendo coyote time,
jump buffer y corner correction) antes de que exista el Player real.

Persona 2 va a crear el Player de verdad en entities/player.py (con vida,
transformación, power-ups). Persona 3 va a crear MenuScene como punto de
entrada real del juego. Cuando eso esté listo, este archivo se borra y
game.py debe apuntar a MenuScene en vez de a PhysicsTestScene.

El guion bajo al inicio del nombre del archivo es a propósito, para que
se note en la carpeta que es algo temporal / interno y no una escena final.
"""

from __future__ import annotations
import pygame

from src.core.scene_base import Scene
from src.core import settings
from src.systems.physics import PhysicsBody
from src.systems import collision
from src.systems.camera import Camera


class _DummyPlayer(PhysicsBody):
    """Un rectángulo controlable. NO es el Player final, solo sirve para probar movimiento."""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, width=14, height=20)


class PhysicsTestScene(Scene):
    def __init__(self, game) -> None:
        self.game = game
        self.player = _DummyPlayer(40, 40)

        # Nivel de prueba con una plataforma angosta para poder probar
        # el corner correction al saltar justo al lado de su esquina.
        self.solids = [
            pygame.Rect(0, 160, 800, 20),     # suelo
            pygame.Rect(120, 120, 50, 8),     # plataforma angosta (probar corner correction)
            pygame.Rect(250, 90, 70, 8),
            pygame.Rect(400, 140, 120, 8),
        ]

        self.camera = Camera(
            view_width=settings.BASE_WIDTH,
            view_height=settings.BASE_HEIGHT,
            level_width=800,
            level_height=180,
        )

    def update(self, dt: float) -> None:
        inp = self.game.input

        self.player.vx = 0.0
        if inp.is_pressed("left"):
            self.player.vx = -settings.MOVE_SPEED
            self.player.facing_right = False
        if inp.is_pressed("right"):
            self.player.vx = settings.MOVE_SPEED
            self.player.facing_right = True

        if inp.is_just_pressed("jump"):
            self.player.request_jump()

        self.player.update_timers(dt)
        self.player.apply_gravity(dt)
        collision.move_and_collide(self.player, dt, self.solids)

        self.camera.update(dt, self.player.rect)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BG)

        for solid in self.solids:
            pygame.draw.rect(surface, settings.COLOR_DEBUG_SOLID, self.camera.apply(solid))

        pygame.draw.rect(surface, settings.COLOR_DEBUG_PLAYER, self.camera.apply(self.player.rect))
