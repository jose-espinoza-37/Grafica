"""
cinematic_scene.py
---------------------
Motor de cutscenes tipo "collage": una serie de "beats" (momentos), cada
uno con una o varias imágenes FIJAS (nunca animadas) y, opcionalmente,
texto que avanza con la acción "confirm".

Si una cinemática necesita "moverse" (ej. Elías caminando hacia la cueva
en la Rotación 4), eso NO pasa aquí — se hace como un tramo de auto-walk
dentro de PlayScene, reusando el gameplay normal y el mismo Player de
Persona 2 (ver play_scene.py, parámetro intro_autowalk_seconds). Este
archivo solo sabe mostrar fotos fijas con texto encima.

Uso típico:
    beats = [
        CinematicBeat(image_path=f"{settings.CINEMATICS_DIR}/lab_alarma.png",
                      lines=["Suenan alarmas. Las luces parpadean."]),
        CinematicBeat(image_path=f"{settings.CINEMATICS_DIR}/rotacion1.png",
                      lines=["ROTACIÓN 1 DETECTADA"]),
    ]
    game.states.switch_to(CinematicScene(game, beats, on_finish=ir_al_nivel_1))
"""

from __future__ import annotations
from dataclasses import dataclass, field
import pygame

from src.core.scene_base import Scene
from src.core import settings
from src.ui.dialogue_box import DialogueBox


@dataclass
class CinematicBeat:
    # Caso simple: una imagen de fondo a pantalla completa.
    image_path: str | None = None
    # Caso "collage": varias fotos en posiciones específicas dentro del
    # mismo beat (ej. el botiquín en una esquina + Elías al centro).
    images: list[tuple[str, pygame.Rect]] = field(default_factory=list)
    # Texto que se muestra sobre la imagen, avanza línea por línea.
    lines: list[str] = field(default_factory=list)


class CinematicScene(Scene):
    def __init__(self, game, beats: list[CinematicBeat], on_finish=None) -> None:
        self.game = game
        self.beats = beats
        self.on_finish = on_finish
        self._beat_index = 0
        self.dialogue = DialogueBox()

    def on_enter(self) -> None:
        self._load_beat(0)

    def _load_beat(self, index: int) -> None:
        self._beat_index = index
        if self._beat_index >= len(self.beats):
            self._finish()
            return

        beat = self.beats[self._beat_index]
        if beat.lines:
            self.dialogue.queue(beat.lines)
        else:
            # Beat sin texto: igual espera un "confirm" para no pasar de
            # largo una imagen que el equipo quiere que se vea un momento.
            self.dialogue.queue([""])

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        if self._beat_index >= len(self.beats):
            return

        if self.game.input.is_just_pressed("confirm"):
            self.dialogue.advance()

        if self.dialogue.finished:
            self._load_beat(self._beat_index + 1)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BLACK)

        if self._beat_index < len(self.beats):
            beat = self.beats[self._beat_index]

            if beat.image_path:
                bg = self.game.assets.get_image(
                    beat.image_path, size=(surface.get_width(), surface.get_height())
                )
                surface.blit(bg, (0, 0))

            for path, rect in beat.images:
                img = self.game.assets.get_image(path, size=(rect.width, rect.height))
                surface.blit(img, rect.topleft)

        self.dialogue.draw(surface, self.game.assets)

    def _finish(self) -> None:
        if self.on_finish:
            self.on_finish()


# ----------------------------------------------------------------------
# Beats reutilizables para el momento del frasco al final de cada nivel
# con peligro (ver sección 5 del documento de diseño).
# ----------------------------------------------------------------------

FRASCO_DIALOGUE_NIVEL_1 = ["Si esto retrasa lo inevitable, que así sea."]


def build_frasco_beat(show_dialogue: bool) -> CinematicBeat:
    """
    Cutscene corta de "Elías bebe un frasco" al final de un nivel con
    peligro. Solo el Nivel 1 muestra el diálogo explicando por qué
    (show_dialogue=True); en los demás niveles se repite el gesto sin texto.
    """
    return CinematicBeat(
        image_path=f"{settings.CINEMATICS_DIR}/frasco.png",
        lines=FRASCO_DIALOGUE_NIVEL_1 if show_dialogue else [],
    )


def build_botiquin_vacio_beat() -> CinematicBeat:
    """Rotación 4: Elías abre el botiquín y está vacío."""
    return CinematicBeat(
        image_path=f"{settings.CINEMATICS_DIR}/botiquin_vacio.png",
        lines=["Como suponía... al menos en esta isla, los efectos tardarán en llegar."],
    )
