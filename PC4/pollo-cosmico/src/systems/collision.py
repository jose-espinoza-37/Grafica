"""
collision.py
--------------
Resuelve colisiones AABB (rectángulos) entre un PhysicsBody y una lista de
rectángulos sólidos del escenario (suelo, plataformas, paredes).

Incluye "corner correction": cuando el jugador salta justo al lado de la
esquina de una plataforma y su cabeza la rozaría apenas, en vez de frenar
el salto en seco y dejarlo caer, se le empuja unos pocos píxeles hacia el
lado libre para que termine subiendo con normalidad. Es un estándar en
juegos de plataformas (se ve, por ejemplo, en Celeste o en los Mario
clásicos) y evita que saltos "casi perfectos" se sientan injustos.

Se mueve primero en X y después en Y por separado (no en diagonal),
que es la forma más simple y predecible de resolver colisiones en 2D.
"""

from __future__ import annotations
import pygame

from src.core import settings
from src.systems.physics import PhysicsBody


def move_and_collide(body: PhysicsBody, dt: float, solids: list[pygame.Rect]) -> None:
    _move_x(body, dt, solids)
    _move_y(body, dt, solids)


def _move_x(body: PhysicsBody, dt: float, solids: list[pygame.Rect]) -> None:
    body.x += body.vx * dt
    rect = body.rect

    for solid in solids:
        if not rect.colliderect(solid):
            continue
        if body.vx > 0:
            rect.right = solid.left
        elif body.vx < 0:
            rect.left = solid.right
        body.vx = 0.0
        body.set_rect_position(rect)
        rect = body.rect


def _move_y(body: PhysicsBody, dt: float, solids: list[pygame.Rect]) -> None:
    body.y += body.vy * dt
    rect = body.rect
    body.on_ground = False

    for solid in solids:
        if not rect.colliderect(solid):
            continue

        if body.vy > 0:
            # Cayendo: aterriza encima de la plataforma.
            rect.bottom = solid.top
            body.on_ground = True
            body.vy = 0.0
            body.set_rect_position(rect)
            body.consume_jump_buffer_if_any()
            rect = body.rect

        elif body.vy < 0:
            # Subiendo: antes de frenar el salto, probar si es solo un
            # roce de esquina que se puede "perdonar" con un empujón lateral.
            if _try_corner_correction(body, rect, solid, solids):
                rect = body.rect
                continue

            rect.top = solid.bottom
            body.vy = 0.0
            body.set_rect_position(rect)
            rect = body.rect


def _try_corner_correction(
    body: PhysicsBody,
    rect: pygame.Rect,
    solid: pygame.Rect,
    solids: list[pygame.Rect],
) -> bool:
    """
    Devuelve True si el choque se resolvió empujando al cuerpo hacia un
    lado (y por lo tanto NO hay que frenar el salto), o False si el golpe
    es un techo real y debe frenarse con normalidad.
    """
    overlap_left = rect.right - solid.left   # qué tanto se mete por el lado izquierdo de la plataforma
    overlap_right = solid.right - rect.left  # qué tanto se mete por el lado derecho

    push = min(overlap_left, overlap_right)
    if push > settings.CORNER_CORRECTION_MAX_PUSH:
        return False  # se mete demasiado profundo: es un techo real, no una esquina

    direction = -1 if overlap_left < overlap_right else 1
    test_rect = rect.copy()
    test_rect.x += direction * push

    if any(test_rect.colliderect(other) for other in solids):
        return False  # empujarlo lo metería en otra plataforma, mejor no arriesgar

    body.set_rect_position(test_rect)
    return True
