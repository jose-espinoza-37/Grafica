"""
game.py
--------
Clase Game: inicializa pygame y la ventana, y corre el loop principal
(eventos -> input -> update -> draw -> presentar en pantalla).

No debería tener lógica de gameplay propia - solo arranca todo y delega
al StateManager. La escena inicial (PhysicsTestScene) es temporal, ver
la nota dentro de ese archivo.
"""

from __future__ import annotations
import sys
import pygame

from src.core import settings
from src.core.asset_manager import AssetManager
from src.core.input_manager import InputManager
from src.core.state_manager import StateManager
from src.audio.audio_manager import AudioManager
from src.utils import pixelate


class Game:
    def __init__(self) -> None:
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            # En algunos entornos sin tarjeta de audio (ej. CI, contenedores)
            # el mixer puede fallar. El juego debe poder seguir sin sonido.
            print("Aviso: no se pudo inicializar el audio. El juego seguirá sin sonido.")

        self.window = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        pygame.display.set_caption(settings.TITLE)

        self.render_surface = pixelate.make_render_surface()
        self.clock = pygame.time.Clock()

        self.assets = AssetManager()
        self.input = InputManager()
        self.states = StateManager()
        self.audio = AudioManager(self.assets)

        self.running = True

    def run(self) -> None:
        from src.scenes.menu_scene import MenuScene
        self.states.switch_to(MenuScene(self))

        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            dt = min(dt, 1 / 30)  # evita "saltos" grandes de física si hay un frame lento

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                self.states.handle_event(event)

            self.input.update(events)
            self.states.update(dt)
            self.states.draw(self.render_surface)

            pixelate.present(self.render_surface, self.window)
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)
