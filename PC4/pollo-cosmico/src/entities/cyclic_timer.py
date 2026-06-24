"""
cyclic_timer.py
-----------------
Temporizador simple para cualquier cosa que alterna entre visible/activo
e invisible/inactivo en ciclos fijos y predecibles: las plataformas que
aparecen y desaparecen en la mitad de playa del Nivel 3, o los enemigos
mutantes que se "reaparecen" en otro punto en ese mismo tramo.

A propósito NO usa números aleatorios: mismo patrón siempre, así el
diseño de nivel puede contar con el timing exacto al colocar plataformas
y enemigos alrededor de él.
"""

from __future__ import annotations


class CyclicTimer:
    def __init__(self, visible_time: float, hidden_time: float, start_visible: bool = True) -> None:
        self.visible_time = visible_time
        self.hidden_time = hidden_time
        self.visible = start_visible
        self._timer = visible_time if start_visible else hidden_time

    def update(self, dt: float) -> bool:
        """Devuelve True solo en el frame exacto en que cambia de estado."""
        self._timer -= dt
        if self._timer <= 0:
            self.visible = not self.visible
            self._timer = self.visible_time if self.visible else self.hidden_time
            return True
        return False
