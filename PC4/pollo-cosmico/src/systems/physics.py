"""
physics.py
-----------
PhysicsBody es la clase base de la que debe heredar cualquier entidad que
se mueve por el mundo con gravedad (sobre todo Player, en entities/player.py
- responsabilidad de Persona 2). Aquí vive:

  - Gravedad y caída.
  - Salto.
  - Coyote time: margen para saltar justo después de salir de una plataforma.
  - Jump buffer: si el jugador presiona saltar un poco antes de tocar el
    suelo, el salto se ejecuta apenas aterriza, en vez de perderse.

La resolución de colisiones contra el escenario (qué hacer cuando el
movimiento choca con una plataforma) vive en collision.py, no aquí.
"""

from __future__ import annotations
import pygame

from src.core import settings


class PhysicsBody:
    def __init__(self, x: float, y: float, width: int, height: int) -> None:
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height

        self.vx = 0.0
        self.vy = 0.0

        self.on_ground = False
        self.facing_right = True

        # Tiempo que lleva sin tocar el suelo (para coyote time)
        self._airborne_time = 0.0
        # Tiempo restante de un salto pedido antes de aterrizar (jump buffer)
        self._jump_buffer_time = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def set_rect_position(self, rect: pygame.Rect) -> None:
        """Usado por collision.py después de ajustar la posición tras un choque."""
        self.x = float(rect.x)
        self.y = float(rect.y)

    # ------------------------------------------------------------------
    # Timers (llamar UNA vez por frame, antes de mover al cuerpo)
    # ------------------------------------------------------------------
    def update_timers(self, dt: float) -> None:
        if self.on_ground:
            self._airborne_time = 0.0
        else:
            self._airborne_time += dt

        if self._jump_buffer_time > 0:
            self._jump_buffer_time -= dt

    def _can_coyote_jump(self) -> bool:
        return (not self.on_ground) and self._airborne_time <= settings.COYOTE_TIME

    # ------------------------------------------------------------------
    # Salto
    # ------------------------------------------------------------------
    def request_jump(self) -> None:
        """
        Llamar cuando el jugador presiona el botón de salto (is_just_pressed).
        Si no se puede saltar en este instante, guarda el intento en el
        jump buffer para que se ejecute apenas el cuerpo toque el suelo.
        """
        if self.on_ground or self._can_coyote_jump():
            self._do_jump()
        else:
            self._jump_buffer_time = settings.JUMP_BUFFER_TIME

    def _do_jump(self) -> None:
        self.vy = settings.JUMP_VELOCITY
        self.on_ground = False
        # Evita que el mismo salto consuma el coyote time dos veces.
        self._airborne_time = settings.COYOTE_TIME + 1.0

    def consume_jump_buffer_if_any(self) -> None:
        """Llamar justo cuando el cuerpo aterriza (lo hace collision.py)."""
        if self._jump_buffer_time > 0:
            self._jump_buffer_time = 0.0
            self._do_jump()

    # ------------------------------------------------------------------
    # Gravedad
    # ------------------------------------------------------------------
    def apply_gravity(self, dt: float) -> None:
        self.vy += settings.GRAVITY * dt
        if self.vy > settings.MAX_FALL_SPEED:
            self.vy = settings.MAX_FALL_SPEED
