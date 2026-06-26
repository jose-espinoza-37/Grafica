"""
audio_manager.py
------------------
Capa simple sobre pygame.mixer. Los efectos de sonido se piden a través
de AssetManager.get_sound(...) (así se cachean); la música de fondo se
maneja aparte con pygame.mixer.music porque pygame solo permite una pista
de música sonando a la vez.

Si un archivo de sonido/música todavía no existe (el audio no está listo),
nada truena: simplemente no se reproduce nada hasta que el archivo exista.
"""

from __future__ import annotations
import os
import pygame

from src.core.asset_manager import AssetManager
from src.core import settings


class AudioManager:
    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        self.sfx_volume = 0.5
        self.music_volume = 0.2
        self.muted = False
        self._current_music: str | None = None
        self.sound_volumes = {
            settings.SFX_JUMP: 0.4,
            settings.SFX_HIT_PLAYER: 0.6,
            settings.SFX_HIT_ENEMY: 0.6,
            settings.SFX_ENEMY_DEFEATED: 0,
            settings.SFX_POWERUP_PLUMA: 0.35,
            settings.SFX_POWERUP_PIO: 0.5,
            settings.SFX_CHECKPOINT: 0.8,
            settings.SFX_FRASCO: 0.8,
            settings.SFX_PAUSE: 0.6,
            settings.SFX_BOOST: 0.7,
        }

    def play_sfx(self, path: str) -> None:
        if self.muted:
            return
        sound = self.assets.get_sound(path)
        if sound is not None:
            volume = self.sound_volumes.get(path, 1.0)
            sound.set_volume(self.sfx_volume * volume)
            sound.play()

    def play_music(self, path: str, loop: bool = True) -> None:
        if self._current_music == path:
            return  # ya está sonando esta pista, no la reinicia
        if not os.path.isfile(path):
            self._current_music = None
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self._current_music = path
        except pygame.error:
            self._current_music = None

    def stop_music(self) -> None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self._current_music = None

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
        try:
            pygame.mixer.music.set_volume(0.0 if muted else self.music_volume)
        except pygame.error:
            pass

    def toggle_mute(self) -> None:
        self.set_muted(not self.muted)
