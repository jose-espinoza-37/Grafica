"""
input_manager.py
-----------------
Capa intermedia entre pygame y el resto del juego.

Por qué existe esto en vez de leer pygame.key.get_pressed() directamente
en cada entidad:
  1. Si cambian el mapeo de teclas, solo se edita settings.ACTION_KEYS.
  2. Permite "input scripteado": durante una cinemática donde el
     personaje camina solo (ver Sección 5 del documento de diseño:
     auto-walk antes de devolver el control al jugador), Persona 3
     puede llamar a set_scripted_input(...) y el Player seguirá
     leyendo input_manager.is_pressed("right") con total normalidad,
     sin saber que no es el jugador real quien lo está presionando.
"""

import pygame
from src.core import settings


class InputManager:
    def __init__(self):
        self._pressed: dict[str, bool] = {a: False for a in settings.ACTION_KEYS}
        self._just_pressed: dict[str, bool] = {a: False for a in settings.ACTION_KEYS}
        self._prev_pressed: dict[str, bool] = {a: False for a in settings.ACTION_KEYS}

        # Cuando no es None, se usa esto en vez del teclado real.
        # Formato: {"right": True, "jump": False, ...}
        self._scripted_input: dict[str, bool] | None = None

    def update(self, events: list[pygame.event.Event]) -> None:
        self._prev_pressed = dict(self._pressed)

        if self._scripted_input is not None:
            self._pressed = dict(self._scripted_input)
        else:
            keys = pygame.key.get_pressed()
            for action, keycodes in settings.ACTION_KEYS.items():
                self._pressed[action] = any(keys[k] for k in keycodes)

        for action in self._pressed:
            self._just_pressed[action] = self._pressed[action] and not self._prev_pressed[action]

    # ------------------------------------------------------------------
    # Consultas (lo que usan Player, UI, etc.)
    # ------------------------------------------------------------------
    def is_pressed(self, action: str) -> bool:
        return self._pressed.get(action, False)

    def is_just_pressed(self, action: str) -> bool:
        return self._just_pressed.get(action, False)

    # ------------------------------------------------------------------
    # Modo cinemática / auto-walk (lo usa CinematicScene / Persona 3)
    # ------------------------------------------------------------------
    def set_scripted_input(self, actions: dict[str, bool]) -> None:
        """
        Activa el modo scripteado. Ejemplo para hacer que el personaje
        camine solo hacia la derecha:
            input_manager.set_scripted_input({"right": True})
        """
        self._scripted_input = {a: False for a in settings.ACTION_KEYS}
        self._scripted_input.update(actions)

    def clear_scripted_input(self) -> None:
        """Devuelve el control al jugador real."""
        self._scripted_input = None

    def is_scripted(self) -> bool:
        return self._scripted_input is not None
