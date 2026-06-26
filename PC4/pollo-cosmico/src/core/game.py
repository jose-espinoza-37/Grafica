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
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Convierte coords de ventana → superficie base (640x360)
                    win_w, win_h = self.window.get_size()
                    scale = min(win_w / settings.BASE_WIDTH, win_h / settings.BASE_HEIGHT)
                    ox = (win_w - int(settings.BASE_WIDTH  * scale)) // 2
                    oy = (win_h - int(settings.BASE_HEIGHT * scale)) // 2
                    bx = (event.pos[0] - ox) / scale
                    by = (event.pos[1] - oy) / scale
                    self.states.handle_mouse_click((bx, by))
                self.states.handle_event(event)

            self.input.update(events)
            self.states.update(dt)
            self.states.draw(self.render_surface)

            pixelate.present(self.render_surface, self.window)
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)
