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


class HUD:
    def draw(self, surface: pygame.Surface, assets, player) -> None:
        self._draw_life_pips(surface, player)
        self._draw_powerups(surface, assets, player)

    def _draw_life_pips(self, surface: pygame.Surface, player) -> None:
        pip_size = 8
        gap = 4
        for i in range(3):
            rect = pygame.Rect(8 + i * (pip_size + gap), 8, pip_size, pip_size)
            hit_already_taken = i < player.stage
            color = (90, 30, 30) if hit_already_taken else settings.COLOR_PLAYER_HUMAN
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, settings.COLOR_WHITE, rect, width=1)

    def _draw_powerups(self, surface: pygame.Surface, assets, player) -> None:
        x = 8
        y = 22

        if player.powerups.double_jump_available:
            pygame.draw.rect(surface, settings.COLOR_POWERUP_DOUBLE_JUMP, (x, y, 10, 10))
            x += 14

        if player.powerups.disguise_active:
            pygame.draw.rect(surface, settings.COLOR_POWERUP_DISGUISE, (x, y, 10, 10))
            font = assets.get_font(None, 9)
            seconds_left = int(player.powerups.disguise_time_left) + 1
            label = font.render(str(seconds_left), False, settings.COLOR_WHITE)
            surface.blit(label, (x + 12, y - 1))
