"""
dialogue_box.py
-----------------
Caja de texto reutilizable. Avanza línea por línea con la acción
"confirm" (Enter/Espacio). La usan CinematicScene (para el texto de las
cutscenes) y también se podría usar suelta en PlayScene si algún día se
necesita un diálogo dentro del gameplay sin pasar por una cinemática completa.
"""

from __future__ import annotations
import pygame

from src.core import settings


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    if not text:
        return [""]

    words = text.split(" ")
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines or [""]


class DialogueBox:
    def __init__(self, lines: list[str] | None = None) -> None:
        self.lines: list[str] = list(lines or [])
        self._index = 0
        self.active = bool(self.lines)

    def queue(self, lines: list[str]) -> None:
        self.lines = list(lines)
        self._index = 0
        self.active = bool(self.lines)

    @property
    def current_text(self) -> str | None:
        if not self.active or self._index >= len(self.lines):
            return None
        return self.lines[self._index]

    @property
    def finished(self) -> bool:
        return not self.active or self._index >= len(self.lines)

    def advance(self) -> None:
        if not self.active:
            return
        self._index += 1
        if self._index >= len(self.lines):
            self.active = False

    def update(self, input_manager) -> None:
        if self.active and input_manager.is_just_pressed("confirm"):
            self.advance()

    def draw(self, surface: pygame.Surface, assets) -> None:
        text = self.current_text
        if text is None:
            return

        box_height = 100
        box_rect = pygame.Rect(10, surface.get_height() - box_height - 12, surface.get_width() - 40, box_height)

        box = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        box.fill((15, 14, 20, 210))
        surface.blit(box, box_rect)
        pygame.draw.rect(surface, settings.COLOR_WHITE, box_rect, 2)

        font = assets.get_font(None, 20)
        wrapped = _wrap_text(text, font, box_rect.width - 16)

        for i, line in enumerate(wrapped[:4]):
            x = box_rect.x + 12
            y = box_rect.y + 10 + i * 22
            shadow = font.render(line, False, (0, 0, 0))
            surface.blit(shadow, (x + 2, y + 2))
            line_surface = font.render(line, False, settings.COLOR_WHITE)
            surface.blit(line_surface, (x, y))

        if pygame.time.get_ticks() % 1000 < 500:
            hint_font = assets.get_font(None, 15)
            hint = hint_font.render("ENTER  >  Continuar", False, (200, 200, 200))
            surface.blit(hint, (box_rect.right - hint.get_width() - 50, box_rect.bottom - 30))
