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

COLLIDER vs SPRITE
  El sprite visual es PLAYER_WIDTH×PLAYER_HEIGHT (28×40 px).
  El collider de física (self.rect) es COLLIDER_W×COLLIDER_H (20×32 px),
  centrado horizontalmente y alineado a los pies del sprite.
  Esto permite que el personaje "encaje" por debajo de plataformas bajas
  que visualmente deberían ser pasables.

  Para convertir entre ambos espacios:
    sprite_x = self.x - COLLIDER_OX
    sprite_y = self.y - COLLIDER_OY
  (self.x / self.y son la esquina superior-izquierda del COLLIDER)

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

_ANIM_FPS = 8.0  # fotogramas de animación por segundo

_WALK_FRAMES = {
    STAGE_HUMANO:        7,
    STAGE_PATAS_POLLO:   7,
    STAGE_ALAS_POLLO:    7,
    STAGE_POLLO_COMPLETO: 4,
}

_SPRITE_KEY = {
    STAGE_HUMANO:        'player_human',
    STAGE_PATAS_POLLO:   'player_patas',
    STAGE_ALAS_POLLO:    'player_alas',
    STAGE_POLLO_COMPLETO: 'player_pollo',
}

# ── Collider reducido ─────────────────────────────────────────────────────
# El sprite visual sigue siendo settings.PLAYER_WIDTH × settings.PLAYER_HEIGHT
# (28×40), pero el rect de física es más pequeño para que el personaje
# pueda pasar por debajo de plataformas bajas que visualmente lo permiten.
COLLIDER_W  = 20   # px  (sprite: 28)
COLLIDER_H  = 32   # px  (sprite: 40)
COLLIDER_OX = (settings.PLAYER_WIDTH  - COLLIDER_W)  // 2   # = 4
COLLIDER_OY = (settings.PLAYER_HEIGHT - COLLIDER_H)          # = 8  (alinear pies)


class Player(PhysicsBody, Entity):
    def __init__(self, x: float, y: float) -> None:
        # PhysicsBody usa el tamaño del COLLIDER, no del sprite
        PhysicsBody.__init__(self, x, y, COLLIDER_W, COLLIDER_H)
        Entity.__init__(self)

        self.powerups = PowerUpManager()
        self.stage = STAGE_HUMANO
        self.defeated = False

        self._air_jump_used = False
        self._invulnerable_timer = 0.0
        self._attack_timer = 0.0
        self._attack_cooldown = 0.0

        self._anim_timer = 0.0
        self._anim_frame = 0

    # ------------------------------------------------------------------
    # Rect del SPRITE (visual), más grande que el collider.
    # Usado solo en draw(); la física siempre opera con self.rect.
    # ------------------------------------------------------------------
    @property
    def sprite_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - COLLIDER_OX,
            self.y - COLLIDER_OY,
            settings.PLAYER_WIDTH,
            settings.PLAYER_HEIGHT,
        )

    # ------------------------------------------------------------------
    # Update principal
    # ------------------------------------------------------------------
    def update(
        self,
        dt: float,
        input_manager,
        solids: list[pygame.Rect],
        gravity_scale: float = 1.0,
    ) -> None:
        if self.defeated:
            return

        self._handle_movement_input(input_manager)
        self._handle_jump_input(input_manager)
        self._handle_attack_input(input_manager)

        self.update_timers(dt)
        self._apply_gravity_scaled(dt, gravity_scale)
        collision.move_and_collide(self, dt, solids)

        if self.on_ground:
            self._air_jump_used = False

        self.powerups.update(dt)
        self._invulnerable_timer  = max(0.0, self._invulnerable_timer  - dt)
        self._attack_timer        = max(0.0, self._attack_timer        - dt)
        self._attack_cooldown     = max(0.0, self._attack_cooldown     - dt)
        self._update_animation(dt)

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
            self.vy = settings.JUMP_VELOCITY
            self._air_jump_used = True
        else:
            self.request_jump()

    def _handle_attack_input(self, input_manager) -> None:
        if input_manager.is_just_pressed("attack") and self._attack_cooldown <= 0:
            self._attack_timer    = settings.PLAYER_ATTACK_DURATION
            self._attack_cooldown = settings.PLAYER_ATTACK_COOLDOWN

    # ------------------------------------------------------------------
    # Física auxiliar
    # ------------------------------------------------------------------
    def _apply_gravity_scaled(self, dt: float, gravity_scale: float) -> None:
        self.vy += settings.GRAVITY * gravity_scale * dt
        self.vy = max(-settings.MAX_FALL_SPEED, min(self.vy, settings.MAX_FALL_SPEED))

    # ------------------------------------------------------------------
    # Ataque
    # ------------------------------------------------------------------
    @property
    def attack_rect(self) -> pygame.Rect | None:
        if self._attack_timer <= 0:
            return None
        rect  = self.rect
        width = settings.PLAYER_ATTACK_RANGE
        x = rect.right if self.facing_right else rect.left - width
        return pygame.Rect(x, rect.y, width, rect.height)

    # ------------------------------------------------------------------
    # Vida / transformación
    # ------------------------------------------------------------------
    def take_hit(self, source_is_mutant: bool = True) -> bool:
        if self.defeated or self._invulnerable_timer > 0:
            return False
        if source_is_mutant and self.powerups.disguise_active:
            return False

        self.stage = min(self.stage + 1, STAGE_POLLO_COMPLETO)
        self.powerups.clear_all()
        self._invulnerable_timer = settings.HIT_INVULNERABILITY_TIME
        self._reset_anim()

        if self.stage >= STAGE_POLLO_COMPLETO:
            self.defeated = True

        return True

    def respawn_at(self, point: tuple[float, float]) -> None:
        self.x, self.y = float(point[0]), float(point[1])
        self.vx = 0.0
        self.vy = 0.0
        self.stage = STAGE_HUMANO
        self.defeated = False
        self.powerups.clear_all()
        self._invulnerable_timer = settings.HIT_INVULNERABILITY_TIME
        self._reset_anim()

    def heal_full(self) -> None:
        self.stage = STAGE_HUMANO
        self.defeated = False

    # ------------------------------------------------------------------
    # Animación
    # ------------------------------------------------------------------
    def _update_animation(self, dt: float) -> None:
        if abs(self.vx) < 1.0:
            self._anim_frame = 0
            self._anim_timer = 0.0
            return
        self._anim_timer += dt
        interval = 1.0 / _ANIM_FPS
        if self._anim_timer >= interval:
            self._anim_timer -= interval
            max_frames = _WALK_FRAMES.get(self.stage, 1)
            self._anim_frame = (self._anim_frame + 1) % max_frames

    def _reset_anim(self) -> None:
        self._anim_frame = 0
        self._anim_timer = 0.0

    # ------------------------------------------------------------------
    # Dibujo — usa sprite_rect (28×40) aunque la física usa rect (20×32)
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, camera, assets=None) -> None:
        draw_rect = camera.apply(self.sprite_rect)

        if assets is not None:
            key   = _SPRITE_KEY.get(self.stage, 'player_human')
            frame = assets.get_player_frame(
                key, self._anim_frame,
                (draw_rect.width, draw_rect.height),
                flip_x=not self.facing_right,
            )
            surface.blit(frame, draw_rect)
        else:
            color = (
                settings.COLOR_PLAYER_HUMAN
                if self.stage == STAGE_HUMANO
                else settings.COLOR_PLAYER_TRANSFORMED
            )
            self.draw_placeholder(surface, camera, self.sprite_rect, color)

        attack_rect = self.attack_rect
        if attack_rect is not None:
            pygame.draw.rect(
                surface, settings.COLOR_WHITE,
                camera.apply(attack_rect), width=1,
            )