"""
powerup_system.py
-------------------
Maneja los 2 power-ups del juego. No es una escena ni un PhysicsBody: es
un componente que el Player guarda (self.powerups = PowerUpManager()) y
consulta cada frame.

Power-ups:

  - "double_jump" (Pluma Cósmica): mientras está activo, el jugador puede
    saltar una vez más en el aire, además del salto normal. No se "gasta"
    al primer uso — se puede usar varias veces dentro del mismo nivel.
    Se pierde solo si el jugador recibe un golpe o termina el nivel.

  - "disguise" (Yo También Digo Pío): durante DISGUISE_DURATION segundos
    los enemigos mutantes no le hacen daño. Tiene su propio temporizador
    y desaparece solo, sin necesidad de recibir un golpe (aunque un golpe
    también lo cancela, eso lo maneja Player.take_hit).

Ambos pueden estar activos a la vez: no hay ninguna regla que los excluya.
"""

from __future__ import annotations
from src.core import settings


class PowerUpManager:
    def __init__(self) -> None:
        self.double_jump_available = False
        self._disguise_timer = 0.0

    @property
    def disguise_active(self) -> bool:
        return self._disguise_timer > 0

    @property
    def disguise_time_left(self) -> float:
        return self._disguise_timer

    def pickup_double_jump(self) -> None:
        self.double_jump_available = True

    def pickup_disguise(self) -> None:
        self._disguise_timer = settings.DISGUISE_DURATION

    def update(self, dt: float) -> None:
        if self._disguise_timer > 0:
            self._disguise_timer = max(0.0, self._disguise_timer - dt)

    def clear_all(self) -> None:
        """Se llama cuando el jugador recibe un golpe: pierde todos los power-ups activos."""
        self.double_jump_available = False
        self._disguise_timer = 0.0
