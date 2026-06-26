"""
pause_scene.py
----------------
Pantalla de pausa. Se apila ENCIMA de PlayScene con states.push(...), no
la reemplaza — por eso el nivel sigue dibujado detrás (StateManager dibuja
toda la pila de abajo hacia arriba). Mientras está pausado, PlayScene.update
no se llama (StateManager solo actualiza la escena de arriba), así que el
juego queda congelado de verdad, no solo visualmente.

Assets que usa (nombres genéricos, ver README_MENU_PAUSA.md):
  - sprites/ui/fondo_2.png  -> panel de fondo de la pausa (no a pantalla
    completa, un recuadro centrado - se ve el juego oscurecido detrás)
  - sprites/ui/boton_1.png / boton_2.png -> igual que en el menú, vía Button

Botones: Reanudar, Reiniciar nivel, Opciones, Menú principal.
"Opciones" se abre con push() (no switch_to), así PlayScene + PauseScene
siguen debajo en la pila y "Volver" desde Opciones solo hace pop() para
regresar exactamente aquí, sin perder la partida.
"""

from __future__ import annotations
import pygame

from src.core.scene_base import Scene
from src.core import settings
from src.ui.button import Button, ButtonMenu


class PauseScene(Scene):
    def __init__(self, game, play_scene) -> None:
        self.game = game
        self.play_scene = play_scene
        center_x = settings.BASE_WIDTH // 2

        self.menu = ButtonMenu([
            Button("Reanudar", center_x - 100, 95, 90, 18, on_select=self._resume),
            Button("Reiniciar nivel", center_x - 100, 118, 90, 18, on_select=self._restart_level),
            Button("Opciones", center_x + 5, 95, 90, 18, on_select=self._open_options),
            Button("Menu principal", center_x + 5, 118, 90, 18, on_select=self._to_menu),
        ])

        self._panel_rect = pygame.Rect(0, 0, 200, 90)
        self._panel_rect.center = (settings.BASE_WIDTH // 2, settings.BASE_HEIGHT // 2)

        # Oscurece el juego de fondo aunque todavía no haya un fondo_2.png
        # real - así la pausa sigue siendo legible incluso sin ese asset.
        self._dim_overlay = pygame.Surface((settings.BASE_WIDTH, settings.BASE_HEIGHT), pygame.SRCALPHA)
        self._dim_overlay.fill((0, 0, 0, 140))

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        if self.game.input.is_just_pressed("pause"):
            self._resume()
            return
        self.menu.update(self.game.input)

    def _resume(self) -> None:
        self.game.states.pop()

    def _restart_level(self) -> None:
        self.play_scene.restart_level()
        self.game.states.pop()

    def _open_options(self) -> None:
        from src.scenes.options_scene import OptionsScene
        self.game.states.push(OptionsScene(self.game, on_back=self.game.states.pop))

    def _to_menu(self) -> None:
        from src.scenes.menu_scene import MenuScene
        self.game.states.switch_to(MenuScene(self.game))

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._dim_overlay, (0, 0))

        panel = self.game.assets.get_image(
            f"{settings.SPRITES_DIR}/ui/fondo_2.png",
            size=(self._panel_rect.width, self._panel_rect.height),
        )
        surface.blit(panel, self._panel_rect.topleft)

        font = self.game.assets.get_font(None, 16)
        label = font.render("PAUSA", False, settings.COLOR_WHITE)
        surface.blit(label, (surface.get_width() // 2 - label.get_width() // 2, self._panel_rect.top + 8))

        self.menu.draw(surface, self.game.assets)