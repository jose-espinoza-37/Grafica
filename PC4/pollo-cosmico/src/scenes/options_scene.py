"""
options_scene.py
-------------------
Pantalla de opciones de audio. Accesible desde dos lugares distintos:

  - MenuScene: OptionsScene(game) -> al volver, switch_to(MenuScene(game)).
  - PauseScene: push(OptionsScene(game, on_back=states.pop)) -> al volver,
    on_back() hace pop() y regresa exactamente a la pausa (la partida
    sigue intacta debajo, PlayScene + PauseScene en la pila).

No tiene slider (el resto del juego usa solo botones discretos, vía
Button/ButtonMenu, igual que menu_scene.py y pause_scene.py) - en su lugar,
"-"/"+" suben o bajan el volumen en pasos de 10%, y un botón alterna
silenciar/activar. Todo se aplica directo sobre game.audio (sfx_volume,
music_volume, set_muted), que ya es la única fuente de verdad del volumen.

Assets que usa (mismo patrón que las demás escenas, ver README_MENU_PAUSA.md):
  - sprites/ui/fondo_2.png -> mismo panel que usa PauseScene
  - sprites/ui/boton_1.png / boton_2.png -> vía Button, automático
"""

from __future__ import annotations
import pygame

from src.core.scene_base import Scene
from src.core import settings
from src.ui.button import Button, ButtonMenu

_VOLUME_STEP = 0.1


class OptionsScene(Scene):
    def __init__(self, game, on_back=None) -> None:
        self.game = game
        # on_back: qué hacer al pulsar "Volver". Si viene de PauseScene, es
        # states.pop (regresa a la pausa). Si viene del menú, no se pasa, y
        # por defecto volvemos directo a MenuScene.
        self.on_back = on_back if on_back is not None else self._back_to_menu

        center_x = settings.BASE_WIDTH // 2

        self.menu = ButtonMenu([
            Button("- Musica", center_x - 130, 90, 80, 18, on_select=self._music_down),
            Button("+ Musica", center_x - 42, 90, 80, 18, on_select=self._music_up),
            Button("- Sonido", center_x - 130, 113, 80, 18, on_select=self._sfx_down),
            Button("+ Sonido", center_x - 42, 113, 80, 18, on_select=self._sfx_up),
            Button("Silenciar", center_x - 130, 136, 172, 18, on_select=self._toggle_mute),
            Button("Volver", center_x - 130, 159, 172, 18, on_select=self._back),
        ])

        self._panel_rect = pygame.Rect(0, 0, 210, 110)
        self._panel_rect.center = (settings.BASE_WIDTH // 2, settings.BASE_HEIGHT // 2)

        self._dim_overlay = pygame.Surface((settings.BASE_WIDTH, settings.BASE_HEIGHT), pygame.SRCALPHA)
        self._dim_overlay.fill((0, 0, 0, 140))

    # ------------------------------------------------------------------
    # Volumen: todo se aplica directo sobre game.audio, que ya clampa/usa
    # estos valores en play_sfx / play_music (ver audio_manager.py).
    # ------------------------------------------------------------------
    def _music_up(self) -> None:
        self.game.audio.music_volume = min(1.0, self.game.audio.music_volume + _VOLUME_STEP)
        self._apply_music_volume()

    def _music_down(self) -> None:
        self.game.audio.music_volume = max(0.0, self.game.audio.music_volume - _VOLUME_STEP)
        self._apply_music_volume()

    def _apply_music_volume(self) -> None:
        # set_muted ya hace pygame.mixer.music.set_volume con el valor correcto
        # según self.muted; reutilizarlo evita duplicar la lógica de mute aquí.
        self.game.audio.set_muted(self.game.audio.muted)

    def _sfx_up(self) -> None:
        self.game.audio.sfx_volume = min(1.0, self.game.audio.sfx_volume + _VOLUME_STEP)

    def _sfx_down(self) -> None:
        self.game.audio.sfx_volume = max(0.0, self.game.audio.sfx_volume - _VOLUME_STEP)

    def _toggle_mute(self) -> None:
        self.game.audio.toggle_mute()

    # ------------------------------------------------------------------
    def _back(self) -> None:
        self.on_back()

    def _back_to_menu(self) -> None:
        from src.scenes.menu_scene import MenuScene
        self.game.states.switch_to(MenuScene(self.game))

    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        if self.game.input.is_just_pressed("pause"):
            self._back()
            return
        self.menu.update(self.game.input)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._dim_overlay, (0, 0))

        panel = self.game.assets.get_image(
            f"{settings.SPRITES_DIR}/ui/fondo_2.png",
            size=(self._panel_rect.width, self._panel_rect.height),
        )
        surface.blit(panel, self._panel_rect.topleft)

        font = self.game.assets.get_font(None, 16)
        title = font.render("OPCIONES", False, settings.COLOR_WHITE)
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, self._panel_rect.top + 8))

        small_font = self.game.assets.get_font(None, 10)
        mute_label = "Silenciado" if self.game.audio.muted else "Sonido activo"
        status = small_font.render(
            f"Musica: {int(self.game.audio.music_volume * 100)}%   "
            f"Sonido: {int(self.game.audio.sfx_volume * 100)}%   {mute_label}",
            False, (220, 220, 220),
        )
        surface.blit(status, (surface.get_width() // 2 - status.get_width() // 2, self._panel_rect.top + 28))

        self.menu.draw(surface, self.game.assets)