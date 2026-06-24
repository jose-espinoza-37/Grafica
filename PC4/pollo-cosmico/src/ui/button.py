"""
button.py
----------
Botón simple para menús (MenuScene, PauseScene). Navegación con
izquierda/derecha y "confirm" para activar — se eligieron esas acciones
porque ya existen en settings.ACTION_KEYS y el juego no tiene una acción
dedicada de "arriba/abajo". Si más adelante el equipo agrega navegación
vertical, sería: agregar "up"/"down" a ACTION_KEYS y usarlas aquí en vez
de left/right.

No incluye soporte de mouse a propósito: mapear la posición del mouse de
la ventana real a coordenadas del render de baja resolución requiere un
cálculo de espacio que vive en utils/pixelate.py (de Persona 1) y no
estaba expuesto todavía. Si lo agregan, ButtonMenu.handle_click ya está
listo para usarlo.
"""

from __future__ import annotations
import pygame

from src.core import settings


class Button:
    def __init__(self, text: str, x: int, y: int, width: int = 90, height: int = 18, on_select=None) -> None:
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.on_select = on_select
        self.focused = False

    def contains_point(self, pos) -> bool:
        return self.rect.collidepoint(pos)

    def activate(self) -> None:
        if self.on_select:
            self.on_select()

    def draw(self, surface: pygame.Surface, assets) -> None:
        bg = settings.COLOR_POWERUP_DOUBLE_JUMP if self.focused else (55, 52, 66)
        fg = settings.COLOR_BLACK if self.focused else settings.COLOR_WHITE

        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, settings.COLOR_WHITE, self.rect, width=1)

        font = assets.get_font(None, 11)
        text_surface = font.render(self.text, False, fg)
        pos = (
            self.rect.centerx - text_surface.get_width() // 2,
            self.rect.centery - text_surface.get_height() // 2,
        )
        surface.blit(text_surface, pos)


class ButtonMenu:
    def __init__(self, buttons: list[Button]) -> None:
        self.buttons = buttons
        self._focus_index = 0
        if self.buttons:
            self.buttons[0].focused = True

    def update(self, input_manager) -> None:
        if not self.buttons:
            return
        if input_manager.is_just_pressed("right"):
            self._move_focus(1)
        if input_manager.is_just_pressed("left"):
            self._move_focus(-1)
        if input_manager.is_just_pressed("confirm"):
            self.buttons[self._focus_index].activate()

    def handle_click(self, pos) -> None:
        """Disponible para cuando se agregue el mapeo de mouse (ver nota arriba)."""
        for i, button in enumerate(self.buttons):
            if button.contains_point(pos):
                self._set_focus(i)
                button.activate()

    def _move_focus(self, delta: int) -> None:
        self._set_focus((self._focus_index + delta) % len(self.buttons))

    def _set_focus(self, index: int) -> None:
        for b in self.buttons:
            b.focused = False
        self._focus_index = index
        self.buttons[index].focused = True

    def draw(self, surface: pygame.Surface, assets) -> None:
        for button in self.buttons:
            button.draw(surface, assets)
