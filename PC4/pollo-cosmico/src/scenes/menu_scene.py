"""
menu_scene.py
--------------
Menú principal. Botones: Jugar (arranca la cinemática inicial + Nivel 1),
Ver Rotación 4 (acceso directo a la secuencia final, útil para probarla
sin jugar todo el juego) y Salir.
"""

from __future__ import annotations
import pygame

from src.core.scene_base import Scene
from src.core import settings
from src.ui.button import Button, ButtonMenu


class MenuScene(Scene):
    def __init__(self, game) -> None:
        self.game = game
        center_x = settings.BASE_WIDTH // 2

        self.menu = ButtonMenu([
            Button("Jugar", center_x - 130, 120, 80, 18, on_select=self._start_game),
            Button("Ver Rotacion 4", center_x - 45, 120, 100, 18, on_select=self._start_rotacion4_demo),
            Button("Salir", center_x + 60, 120, 70, 18, on_select=self._quit),
        ])

    def on_enter(self) -> None:
        self.game.audio.play_music(f"{settings.AUDIO_DIR}/music/menu.ogg")

    def _start_game(self) -> None:
        from src.scenes.intro_flow import start_new_game
        start_new_game(self.game)

    def _start_rotacion4_demo(self) -> None:
        from src.scenes.intro_flow import start_rotacion4_demo
        start_rotacion4_demo(self.game)

    def _quit(self) -> None:
        self.game.running = False

    def update(self, dt: float) -> None:
        self.menu.update(self.game.input)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BG)

        title_font = self.game.assets.get_font(None, 18)
        title = title_font.render("EL POLLO COSMICO", False, settings.COLOR_WHITE)
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 60))

        subtitle_font = self.game.assets.get_font(None, 10)
        subtitle = subtitle_font.render(
            '"La vida da vueltas como un pollo a la brasa"', False, (190, 190, 190)
        )
        surface.blit(subtitle, (surface.get_width() // 2 - subtitle.get_width() // 2, 82))

        self.menu.draw(surface, self.game.assets)
