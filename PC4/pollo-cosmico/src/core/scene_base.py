"""
scene_base.py
--------------
Interfaz mínima que toda escena debe cumplir (MenuScene, PlayScene,
CinematicScene, PauseScene, GameOverScene...). El StateManager solo
sabe llamar estos métodos, no le importa qué hace cada escena por dentro.

Persona 2 y 3: hereden de esta clase y sobreescriban lo que necesiten.
No es obligatorio sobreescribir todo (por defecto no hacen nada).
"""

from __future__ import annotations
import pygame


class Scene:
    def on_enter(self) -> None:
        """Se llama una vez al entrar a esta escena (StateManager.switch_to / push)."""

    def on_exit(self) -> None:
        """Se llama una vez al salir de esta escena."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Eventos puntuales de pygame (cerrar ventana, click de mouse, etc.)."""

    def update(self, dt: float) -> None:
        """Lógica de la escena. dt está en segundos."""

    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja la escena sobre 'surface' (la superficie de baja resolución)."""
