"""
player.py
----------
El personaje del jugador (Dr. Elías Vega). Hereda de PhysicsBody (Persona 1)
para la gravedad/salto/coyote-time/jump-buffer, y le agrega:

  - Sistema de vida por transformación: 3 golpes de tolerancia.
      Golpe 1 -> patas de pollo
      Golpe 2 -> alas de pollo
      Golpe 3 -> pollo completo (derrota, hay que reaparecer en el checkpoint)
  - Power-ups (Pluma Cósmica y Yo También Digo Pío) vía PowerUpManager.
  - Un ataque simple de corto alcance (mecánica de tutorial del Nivel 1).
  - Reaparecer en un checkpoint, restaurando la forma humana.

NOTA sobre cinemáticas con auto-walk: este archivo NO necesita ningún
código especial para eso. Si Persona 3 activa un input scripteado en el
InputManager (game.input.set_scripted_input(...)), Player simplemente lo
lee igual que un input real a través de los mismos métodos is_pressed/
is_just_pressed - no hace falta ninguna rama de código adicional aquí.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.systems.physics import PhysicsBody
from src.systems import collision
from src.systems.powerup_system import PowerUpManager
from src.entities.entity_base import Entity

# Etapas de transformación, de menos a más afectado por La Brasa.
STAGE_HUMANO = 0
STAGE_PATAS_POLLO = 1
STAGE_ALAS_POLLO = 2
STAGE_POLLO_COMPLETO = 3


class Player(PhysicsBody, Entity):
    def __init__(self, x: float, y: float) -> None:
        PhysicsBody.__init__(self, x, y, settings.PLAYER_WIDTH, settings.PLAYER_HEIGHT)
        Entity.__init__(self)

        self.powerups = PowerUpManager()
        self.stage = STAGE_HUMANO
        self.defeated = False

        self._air_jump_used = False        # si ya usó el salto extra de Pluma Cósmica en este aire
        self._invulnerable_timer = 0.0      # evita golpes repetidos del mismo enemigo en el mismo frame
        self._attack_timer = 0.0            # cuánto le queda activo al hitbox de ataque
        self._attack_cooldown = 0.0

    # ------------------------------------------------------------------
    # Update principal: llamar una vez por frame desde PlayScene.
    # gravity_scale sirve para las zonas de gravedad alterada del Nivel 2
    # (1.0 = normal, valores distintos los da GravityZone).
    # ------------------------------------------------------------------
    def update(
        self,
        dt: float,
        input_manager,
        solids: list[pygame.Rect],
        gravity_scale: float = 1.0,
    ) -> None:
        if self.defeated:
            return  # a la espera de que la escena llame a respawn_at(...)

        self._handle_movement_input(input_manager)
        self._handle_jump_input(input_manager)
        self._handle_attack_input(input_manager)

        self.update_timers(dt)
        self._apply_gravity_scaled(dt, gravity_scale)
        collision.move_and_collide(self, dt, solids)

        if self.on_ground:
            self._air_jump_used = False

        self.powerups.update(dt)
        self._invulnerable_timer = max(0.0, self._invulnerable_timer - dt)
        self._attack_timer = max(0.0, self._attack_timer - dt)
        self._attack_cooldown = max(0.0, self._attack_cooldown - dt)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def _handle_movement_input(self, input_manager) -> None:
        self.vx = 0.0
        if input_manager.is_pressed("left"):
            self.vx = -settings.MOVE_SPEED
            self.facing_right = False
        if input_manager.is_pressed("right"):
            self.vx = settings.MOVE_SPEED
            self.facing_right = True

    def _handle_jump_input(self, input_manager) -> None:
        if not input_manager.is_just_pressed("jump"):
            return

        if self.on_ground or self._can_coyote_jump():
            self.request_jump()
            self._air_jump_used = False
        elif self.powerups.double_jump_available and not self._air_jump_used:
            # Salto extra de Pluma Cósmica: no consume el power-up, solo se
            # puede usar una vez por cada vez que está en el aire.
            self.vy = settings.JUMP_VELOCITY
            self._air_jump_used = True
        else:
            # Ni suelo, ni coyote time, ni salto extra disponible:
            # se guarda el intento en el jump buffer por si aterriza enseguida.
            self.request_jump()

    def _handle_attack_input(self, input_manager) -> None:
        if input_manager.is_just_pressed("attack") and self._attack_cooldown <= 0:
            self._attack_timer = settings.PLAYER_ATTACK_DURATION
            self._attack_cooldown = settings.PLAYER_ATTACK_COOLDOWN

    # ------------------------------------------------------------------
    # Física auxiliar (gravedad con escala, para las zonas del Nivel 2)
    # ------------------------------------------------------------------
    def _apply_gravity_scaled(self, dt: float, gravity_scale: float) -> None:
        self.vy += settings.GRAVITY * gravity_scale * dt
        self.vy = max(-settings.MAX_FALL_SPEED, min(self.vy, settings.MAX_FALL_SPEED))

    # ------------------------------------------------------------------
    # Ataque (mecánica de tutorial del Nivel 1)
    # ------------------------------------------------------------------
    @property
    def attack_rect(self) -> pygame.Rect | None:
        """Devuelve el hitbox de ataque activo, o None si no está atacando.
        PlayScene lo compara contra enemy.rect para aplicar daño."""
        if self._attack_timer <= 0:
            return None
        rect = self.rect
        width = settings.PLAYER_ATTACK_RANGE
        x = rect.right if self.facing_right else rect.left - width
        return pygame.Rect(x, rect.y, width, rect.height)

    # ------------------------------------------------------------------
    # Vida / transformación
    # ------------------------------------------------------------------
    def take_hit(self, source_is_mutant: bool = True) -> bool:
        """
        Llamar cuando un enemigo golpea al jugador. Devuelve True si el
        golpe se aplicó de verdad (para que quien llama reproduzca sonido,
        sacuda la cámara, etc.), o False si no pasó nada (invulnerable o
        protegido por el disfraz).
        """
        if self.defeated or self._invulnerable_timer > 0:
            return False

        if source_is_mutant and self.powerups.disguise_active:
            return False  # el disfraz de "Yo También Digo Pío" lo protege

        self.stage = min(self.stage + 1, STAGE_POLLO_COMPLETO)
        self.powerups.clear_all()
        self._invulnerable_timer = settings.HIT_INVULNERABILITY_TIME

        if self.stage >= STAGE_POLLO_COMPLETO:
            self.defeated = True

        return True

    def respawn_at(self, point: tuple[float, float]) -> None:
        """Llamar desde la escena cuando defeated=True, usando el último checkpoint."""
        self.x, self.y = float(point[0]), float(point[1])
        self.vx = 0.0
        self.vy = 0.0
        self.stage = STAGE_HUMANO
        self.defeated = False
        self.powerups.clear_all()
        self._invulnerable_timer = settings.HIT_INVULNERABILITY_TIME

    def heal_full(self) -> None:
        """Llamar al beber un frasco al final de nivel: revierte cualquier
        transformación y lo deja completamente humano para el siguiente nivel."""
        self.stage = STAGE_HUMANO
        self.defeated = False

    # ------------------------------------------------------------------
    # Dibujo (placeholder hasta tener los sprites por etapa)
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, camera) -> None:
        color = settings.COLOR_PLAYER_HUMAN if self.stage == STAGE_HUMANO else settings.COLOR_PLAYER_TRANSFORMED
        self.draw_placeholder(surface, camera, self.rect, color)

        attack_rect = self.attack_rect
        if attack_rect is not None:
            pygame.draw.rect(surface, settings.COLOR_WHITE, camera.apply(attack_rect), width=1)
