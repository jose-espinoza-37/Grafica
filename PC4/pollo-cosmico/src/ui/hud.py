"""
hud.py
-------
HUD del gameplay. Dos cosas:

  1. Indicador de vida/transformación: 3 "pips" que representan los 3
     golpes de tolerancia. Se van marcando conforme el jugador se
     transforma (patas -> alas -> pollo completo).
  2. Power-ups activos: un ícono si tiene Pluma Cósmica disponible, y
     otro (con segundos restantes) si el disfraz "Yo También Digo Pío"
     está activo.

Todo dibujado como rectángulos de color (placeholder) hasta que existan
los íconos finales - no depende de ningún sprite en particular.
"""

from __future__ import annotations
import pygame

from src.core import settings


_PIP_W = 12
_PIP_H = 14
_PIP_GAP = 4
_ICON_SIZE = 14   # power-up icon on canvas (28px on window)


class HUD:
    def draw(self, surface: pygame.Surface, assets, player) -> None:
        self._draw_life_pips(surface, player)
        self._draw_powerups(surface, assets, player)

    def _draw_life_pips(self, surface: pygame.Surface, player) -> None:
        for i in range(3):
            x = 8 + i * (_PIP_W + _PIP_GAP)
            y = 6
            filled = i >= player.stage
            color  = (220, 55, 65) if filled else (55, 20, 25)
            border = (255, 130, 140) if filled else (90, 45, 50)
            pygame.draw.rect(surface, color,  (x, y, _PIP_W, _PIP_H), border_radius=4)
            pygame.draw.rect(surface, border, (x, y, _PIP_W, _PIP_H), width=1, border_radius=4)

    def _draw_powerups(self, surface: pygame.Surface, assets, player) -> None:
        x = 8
        y = 6 + _PIP_H + 4   # justo debajo de las vidas

        if player.powerups.double_jump_available:
            self._draw_icon(surface, assets, 'pluma_cosmica', x, y,
                            settings.COLOR_POWERUP_DOUBLE_JUMP)
            x += _ICON_SIZE + 4

        if player.powerups.disguise_active:
            self._draw_icon(surface, assets, 'disfraz_pio', x, y,
                            settings.COLOR_POWERUP_DISGUISE)
            font = assets.get_font(None, 8)
            seconds_left = int(player.powerups.disguise_time_left) + 1
            label = font.render(str(seconds_left), False, settings.COLOR_WHITE)
            surface.blit(label, (x + _ICON_SIZE + 2, y + 2))

    def _draw_icon(self, surface, assets, key, x, y, fallback_color) -> None:
        frame = assets.get_player_frame(key, 0, (_ICON_SIZE, _ICON_SIZE))
        surface.blit(frame, (x, y))
        # Borde sutil para distinguirlo del fondo
        pygame.draw.rect(surface, fallback_color, (x, y, _ICON_SIZE, _ICON_SIZE), width=1)
