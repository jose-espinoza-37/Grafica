"""
gameover_scene.py
-------------------
En este diseño no existe una condición real de "game over" durante el
gameplay — morir solo manda al jugador al último checkpoint, sin límite
de intentos (a propósito, ver el documento de diseño: anti-frustración
de jam). Esta escena se reutiliza entonces para los cierres de pantalla
completa: la luz blanca tras la última rotación, o cualquier "pantalla
final" que el equipo necesite más adelante.

hold_seconds: cuánto tiempo se queda solo el color de fondo (silencio,
sin texto ni input) antes de mostrar el mensaje y aceptar "confirm" para
volver al menú. Para la luz blanca final, eso simula el "silencio, luego
oscuridad" del documento de diseño.
"""

from __future__ import annotations
import pygame

from src.core.scene_base import Scene
from src.core import settings


class GameOverScene(Scene):
    def __init__(
        self,
        game,
        message: str = "FIN",
        bg_color: tuple[int, int, int] = settings.COLOR_WHITE,
        text_color: tuple[int, int, int] = settings.COLOR_BLACK,
        hold_seconds: float = 3.0,
        on_finish=None,
        auto_continue: bool = False,
    ) -> None:
        self.game = game
        self.message = message
        self.bg_color = bg_color
        self.text_color = text_color
        self._timer = hold_seconds
        self.on_finish = on_finish
        self.auto_continue = auto_continue

    def update(self, dt: float) -> None:
        if self._timer > 0:
            self._timer -= dt
            return
        if self.auto_continue:
            self._trigger_finish()
            return
        if self.game.input.is_just_pressed("confirm"):
            self._trigger_finish()

    def _trigger_finish(self) -> None:
        if self.on_finish:
            self.on_finish()
        else:
            from src.scenes.menu_scene import MenuScene
            self.game.states.switch_to(MenuScene(self.game))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self.bg_color)
        if self._timer <= 0:
            font = self.game.assets.get_font(None, 14)
            label = font.render(self.message, False, self.text_color)
            surface.blit(
                label,
                (surface.get_width() // 2 - label.get_width() // 2, surface.get_height() // 2),
            )
