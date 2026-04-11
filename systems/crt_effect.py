"""CRT helpers — scanlines e granulação."""

import pygame
import random


def draw_scanlines(surface: pygame.Surface, spacing: int = 4):
    """Linhas horizontais a cada `spacing` pixels."""
    w, h = surface.get_size()
    for y in range(0, h, spacing):
        pygame.draw.line(surface, (0, 0, 0, 35), (0, y), (w, y))


def draw_film_grain(surface: pygame.Surface, count: int = 50):
    """Pixels aleatórios simulando granulação."""
    w, h = surface.get_size()
    for _ in range(count):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        v = random.randint(200, 255)
        surface.set_at((x, y), (v, v, v))
