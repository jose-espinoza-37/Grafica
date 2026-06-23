"""
state_manager.py
------------------
Controla qué escena está activa y le delega update/draw/handle_event.
Usa una pila (no solo "la escena actual") para poder apilar cosas como
Pausa encima de PlayScene sin perder el estado del juego de fondo.
"""

from __future__ import annotations
import pygame

from src.core.scene_base import Scene


class StateManager:
    def __init__(self) -> None:
        self._stack: list[Scene] = []

    @property
    def current(self) -> Scene | None:
        return self._stack[-1] if self._stack else None

    def switch_to(self, scene: Scene) -> None:
        """Reemplaza toda la pila por una sola escena. Ej: Menu -> PlayScene."""
        for old in self._stack:
            old.on_exit()
        self._stack = [scene]
        scene.on_enter()

    def push(self, scene: Scene) -> None:
        """Apila una escena encima de la actual sin destruirla. Ej: abrir Pausa."""
        self._stack.append(scene)
        scene.on_enter()

    def pop(self) -> None:
        """Quita la escena de encima y vuelve a la anterior. Ej: cerrar Pausa."""
        if self._stack:
            old = self._stack.pop()
            old.on_exit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current is not None:
            self.current.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current is not None:
            self.current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        # Se dibuja toda la pila de abajo hacia arriba: así si hay una
        # PauseScene encima, PlayScene sigue visible detrás (semi-transparente,
        # por ejemplo), en vez de tapar todo con una pantalla negra.
        for scene in self._stack:
            scene.draw(surface)
