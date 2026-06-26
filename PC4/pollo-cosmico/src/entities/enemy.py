"""
enemy.py
---------
Enemigo simple para todos los niveles con peligro:

  - Nivel 1: robots de seguridad. is_mutant=False (sin pico, el disfraz no
    aplica contra ellos, pero tampoco está disponible en ese nivel).
  - Nivel 2 y Nivel 3: mutantes con pico de gallina. is_mutant=True, así
    el power-up "Yo También Digo Pío" tiene sentido contra ellos.

Patrulla en línea recta entre patrol_min_x y patrol_max_x (se asume que
ya está parado sobre una plataforma puesta por el diseño de nivel - no
tiene gravedad propia, para mantenerlo simple). Ataca por contacto simple
con el jugador, con cooldown para no golpearlo todos los frames.

reappear_cycle es opcional: si se le pasa un CyclicTimer, el enemigo se
"apaga" (no patrulla, no ataca, no se dibuja) y vuelve a aparecer en
reappear_point cuando el ciclo lo indique - usado en la mitad de playa
del Nivel 3 para simular el efecto de distorsión temporal sin teletransporte
real ni duplicación.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.entities.entity_base import Entity
from src.entities.cyclic_timer import CyclicTimer


class Enemy(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        width: int = 16,
        height: int = 20,
        patrol_min_x: float | None = None,
        patrol_max_x: float | None = None,
        speed: float = settings.ENEMY_PATROL_SPEED,
        is_mutant: bool = True,
        reappear_cycle: CyclicTimer | None = None,
    ) -> None:
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.speed = speed
        self.direction = 1
        self.patrol_min_x = patrol_min_x if patrol_min_x is not None else x - 30
        self.patrol_max_x = patrol_max_x if patrol_max_x is not None else x + 30
        self.is_mutant = is_mutant

        self.reappear_cycle = reappear_cycle
        self.reappear_point = (x, y)

        self._attack_cooldown = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    @property
    def active(self) -> bool:
        """Falso mientras está en su fase 'invisible' del ciclo (si tiene uno)."""
        return self.reappear_cycle.visible if self.reappear_cycle else True

    def update(self, dt: float) -> None:
        if self.reappear_cycle is not None:
            changed = self.reappear_cycle.update(dt)
            if changed and self.reappear_cycle.visible:
                self.x, self.y = self.reappear_point
            if not self.reappear_cycle.visible:
                return  # invisible: no patrulla, no ataca, no se dibuja

        self._patrol(dt)
        self._attack_cooldown = max(0.0, self._attack_cooldown - dt)

    def _patrol(self, dt: float) -> None:
        self.x += self.speed * self.direction * dt
        if self.x <= self.patrol_min_x:
            self.x = self.patrol_min_x
            self.direction = 1
        elif self.x >= self.patrol_max_x:
            self.x = self.patrol_max_x
            self.direction = -1

    def try_attack(self, player) -> bool:
        """
        Llamar desde PlayScene cuando enemy.rect colisiona con player.rect.
        Devuelve True si el golpe se aplicó (para feedback de Persona 3).
        """
        if not self.active or self._attack_cooldown > 0:
            return False
        applied = player.take_hit(source_is_mutant=self.is_mutant)
        if applied:
            self._attack_cooldown = settings.ENEMY_ATTACK_COOLDOWN
        return applied

    def take_damage(self) -> None:
        """Llamar cuando el ataque del jugador lo golpea. Un golpe basta (jam-friendly)."""
        self.alive = False

    def draw(self, surface: pygame.Surface, camera, assets=None) -> None:
        if not self.active:
            return
        if assets is not None:
            key = 'enemy_mutante' if self.is_mutant else 'enemy_robot'
            rect = camera.apply(self.rect)
            # facing_right no existe en Enemy hoy; se usa direction (1 = derecha)
            # como aproximacion para el flip horizontal del sprite.
            frame = assets.get_player_frame(key, 0, (rect.width, rect.height), flip_x=self.direction < 0)
            surface.blit(frame, rect)
        else:
            color = settings.COLOR_ENEMY_MUTANT if self.is_mutant else settings.COLOR_ENEMY_ROBOT
            self.draw_placeholder(surface, camera, self.rect, color)