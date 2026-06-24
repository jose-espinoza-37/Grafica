"""
pause_scene.py
----------------
Pantalla de pausa. Se apila ENCIMA de PlayScene con states.push(...), no
la reemplaza — por eso el nivel sigue dibujado detrás (StateManager dibuja
toda la pila de abajo hacia arriba). Mientras está pausado, PlayScene.update
no se llama (StateManager solo actualiza la escena de arriba), así que el
juego queda congelado de verdad, no solo visualmente.
"""

from __future__ import annotations
import pygame

from src.core.scene_base import Scene
from src.core import settings
from src.ui.button import Button, ButtonMenu


class PauseScene(Scene):
    def __init__(self, game) -> None:
        self.game = game
        center_x = settings.BASE_WIDTH // 2

        self.menu = ButtonMenu([
            Button("Reanudar", center_x - 100, 100, 90, 18, on_select=self._resume),
            Button("Menu principal", center_x + 5, 100, 100, 18, on_select=self._to_menu),
        ])

        self._overlay = pygame.Surface((settings.BASE_WIDTH, settings.BASE_HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        if self.game.input.is_just_pressed("pause"):
            self._resume()
            return
        self.menu.update(self.game.input)

    def _resume(self) -> None:
        self.game.states.pop()

    def _to_menu(self) -> None:
        from src.scenes.menu_scene import MenuScene
        self.game.states.switch_to(MenuScene(self.game))

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._overlay, (0, 0))

        font = self.game.assets.get_font(None, 16)
        label = font.render("PAUSA", False, settings.COLOR_WHITE)
        surface.blit(label, (surface.get_width() // 2 - label.get_width() // 2, 65))

        self.menu.draw(surface, self.game.assets)
