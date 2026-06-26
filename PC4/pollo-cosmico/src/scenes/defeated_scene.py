"""
defeated_scene.py
-----------------
Pantalla de derrota que aparece cuando el jugador recibe el tercer golpe
(player.defeated=True). Se apila encima de PlayScene (push), así el fondo
del nivel sigue visible pero oscurecido.

  - "Empezar desde 0":            llama on_restart() → nueva PlayScene fresca.
  - "Continuar desde checkpoint": llama on_checkpoint() → respawn en el checkpoint
                                   (opción deshabilitada si no hay checkpoint activo).
"""
from __future__ import annotations
import pygame

from src.core.scene_base import Scene
from src.core import settings


class DefeatedScene(Scene):
    _OVERLAY_ALPHA = 170
    _HOLD_BEFORE_INPUT = 0.9   # gracia para evitar selección accidental

    def __init__(
        self,
        game,
        player,
        on_restart,
        on_checkpoint,
        checkpoint_available: bool = False,
    ) -> None:
        self.game = game
        self.player = player
        self.on_restart = on_restart
        self.on_checkpoint = on_checkpoint
        self.checkpoint_available = checkpoint_available

        self._selected = 0
        self._hold_timer = self._HOLD_BEFORE_INPUT

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._hold_timer > 0:
            return
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
            self._selected = 0
        elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
            if self.checkpoint_available:
                self._selected = 1
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._confirm()

    def update(self, dt: float) -> None:
        self._hold_timer = max(0.0, self._hold_timer - dt)

    def _confirm(self) -> None:
        if self._selected == 0:
            self.on_restart()
        else:
            self.on_checkpoint()

    def draw(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_width(), surface.get_height()
        cx = sw // 2

        # Oscurecer el fondo (PlayScene queda visible abajo)
        overlay = pygame.Surface((sw, sh))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(self._OVERLAY_ALPHA)
        surface.blit(overlay, (0, 0))

        # Sprite del pollo completo (2× el tamaño de gameplay → impacto visual)
        sprite_w, sprite_h = 56, 80
        frame = self.game.assets.get_player_frame(
            'player_pollo', 0, (sprite_w, sprite_h), flip_x=False
        )
        sprite_top = sh // 2 - sprite_h - 28
        surface.blit(frame, (cx - sprite_w // 2, sprite_top))

        # Título
        font_title = self.game.assets.get_font(None, 20)
        title = font_title.render("DERROTA", False, (220, 50, 50))
        title_y = sprite_top + sprite_h + 8
        surface.blit(title, (cx - title.get_width() // 2, title_y))

        # Opciones
        font_opt = self.game.assets.get_font(None, 11)
        options = [
            ("Empezar desde 0", True),
            ("Continuar desde checkpoint", self.checkpoint_available),
        ]
        for i, (text, enabled) in enumerate(options):
            if not enabled:
                color = (70, 70, 70)
            elif i == self._selected:
                color = (255, 225, 60)
            else:
                color = (190, 190, 190)
            label = font_opt.render(text, False, color)
            y = title_y + 28 + i * 20
            surface.blit(label, (cx - label.get_width() // 2, y))

        # Pista de controles (aparece después de la gracia)
        if self._hold_timer <= 0:
            font_hint = self.game.assets.get_font(None, 8)
            hint = font_hint.render(
                "Flechas / WASD para navegar  ·  ENTER o ESPACIO para confirmar",
                False,
                (100, 100, 100),
            )
            surface.blit(hint, (cx - hint.get_width() // 2, sh - 14))
