#!/usr/bin/env python3

"""
O Zelador do Vacuo -- Prototipo Pygame
=======================================
Uma sala de controle claustrofobica.
Arraste o mouse horizontalmente sobre o painel de radio para sintonizar.
"""

import pygame
import sys
import os
import math
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from managers.game_manager import GameManager
from managers.sanity_manager import SanityManager
from managers.maintenance_manager import MaintenanceManager
from managers.day_manager import DayManager
from systems.radio_system import RadioSystem
from systems.radar_system import RadarSystem


# -- Configuracoes --
WIDTH = 1024
HEIGHT = 768
FPS = 60

# Cores
BLACK = (0, 0, 0)
DARK_BG = (5, 8, 5)
GREEN = (0, 255, 51)
DIM_GREEN = (0, 90, 13)
MED_GREEN = (102, 153, 77)
OFF_GREEN = (51, 77, 38)
WARN_RED = (180, 40, 40)


def draw_scanlines(surface: pygame.Surface):
    """Scanlines leves -- so a cada 4 pixels."""
    w, h = surface.get_size()
    for y in range(0, h, 4):
        pygame.draw.line(surface, (0, 0, 0, 30), (0, y), (w, y))


def draw_vignette(surface: pygame.Surface, intensity: float):
    """Vinheta escura nas bordas proporcional a intensidade."""
    if intensity < 0.05:
        return
    w, h = surface.get_size()
    cx, cy = w // 2, h // 2
    max_r = int(math.sqrt(cx * cx + cy * cy))
    steps = 20
    for i in range(steps, 0, -1):
        r = int(max_r * (i / steps))
        progress = i / steps
        if progress < intensity:
            alpha = int((1.0 - progress / intensity) * 40)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 0, 0, alpha), (r, r), r)
            surface.blit(s, (cx - r, cy - r))


def draw_film_grain(surface: pygame.Surface, amount: int = 50):
    """Granulacao leve -- alguns pixels aleatorios."""
    w, h = surface.get_size()
    for _ in range(amount):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        v = random.randint(200, 255)
        surface.set_at((x, y), (v, v, v, 15))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("O Zelador do Vacuo")
    clock = pygame.time.Clock()

    # -- Instanciar managers --
    gm = GameManager.get()
    sanity_mgr = SanityManager(gm)

    # -- Layout --
    panel_margin = 40
    left_w = 380
    right_w = WIDTH - panel_margin * 2 - left_w - 20

    radar_size = 340
    radar_x = panel_margin + (left_w - radar_size) // 2
    radar_y = panel_margin + 30

    radio_x = panel_margin + left_w + 20
    radio_y = panel_margin + 10
    radio_w = right_w
    radio_h = 170

    # Painel de manutencao (lado direito, abaixo do radio)
    maint_x = radio_x
    maint_y = radio_y + radio_h + 15
    maint_w = radio_w

    # -- Instanciar sistemas --
    day_mgr = DayManager(gm)
    radar = RadarSystem(radar_x, radar_y, radar_size, gm, gm.ACTIVATION_DELAY, day_mgr)
    radio = RadioSystem(radio_x, radio_y, radio_w, radio_h, gm)
    maint = MaintenanceManager(maint_x, maint_y, maint_w, gm)

    # -- Fontes --
    font_title = pygame.font.SysFont("monospace", 14, bold=True)
    font_small = pygame.font.SysFont("monospace", 11)
    font_status = pygame.font.SysFont("monospace", 12)
    font_tiny = pygame.font.SysFont("monospace", 10)

    # -- Loop principal --
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # -- Eventos --
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            else:
                radio.handle_event(event)
                maint.handle_event(event)

        # -- Updates --
        day_mgr.update(dt)
        gm.update_station_change(dt)    # Feature 1 + 3
        gm.update_sanity(dt)
        gm.try_show_message(dt)
        gm.check_radio_tuned()
        sanity_mgr.update(dt)
        maint.update(dt)
        radar.update(dt)

        # -- Shake offset --
        ox, oy = sanity_mgr.shake_offset

        # -- Render --
        screen.fill(DARK_BG)

        # -- Painel console --
        panel_rect = pygame.Rect(panel_margin, panel_margin,
                                 WIDTH - panel_margin * 2,
                                 HEIGHT - panel_margin * 2)
        pygame.draw.rect(screen, (8, 8, 8), panel_rect, border_radius=6)
        pygame.draw.rect(screen, DIM_GREEN, panel_rect, 1, border_radius=6)

        # -- Radar --
        radar_label = font_title.render("[ RADAR DE VARREDURA ]", True, GREEN)
        screen.blit(radar_label, (radar_x + ox, radar_y - 24 + oy))

        radar.draw_x = ox
        radar.draw_y = oy
        radar.draw(screen)

        # -- Radio --
        radio.draw_offset_x = ox
        radio.draw_offset_y = oy
        radio.draw(screen)

        # -- Manutencao --
        maint.draw(screen, ox, oy)

        # -- Info inferior esquerdo --
        info_y = radar_y + radar_size + 15 + oy
        info_x = radar_x + ox

        # Feature 1: frequencia alvo
        target_text = font_tiny.render(
            f"ALVO: {gm.target_frequency:.1f} MHz", True, OFF_GREEN)
        screen.blit(target_text, (info_x, info_y))

        # Feature 3: tempo de jogo e intervalo de troca
        mins = int(gm.elapsed_time) // 60
        secs = int(gm.elapsed_time) % 60
        interval = gm.station_change_interval
        time_text = font_tiny.render(
            f"TEMPO: {mins:02d}:{secs:02d}  |  TROCA: {interval:.0f}s", True, OFF_GREEN)
        screen.blit(time_text, (info_x, info_y + 16))

        # Feature 2: tolerancia e ameaca
        tolerance = gm.radio_tolerance
        threat = gm.entity_threat

        if threat > 0.5:
            threat_color = WARN_RED
        elif threat > 0.2:
            threat_color = (200, 180, 0)
        else:
            threat_color = OFF_GREEN

        threat_text = font_tiny.render(
            f"AMEACA: {threat:.0%}  |  TOLERANCIA: +/-{tolerance:.2f} MHz", True, threat_color)
        screen.blit(threat_text, (info_x, info_y + 32))

        # -- Display do dia (logo abaixo dos botoes, SEM shake) --
        day_box_x = maint_x
        day_box_y = maint.rect.y + maint.rect.height + 8
        day_box_w = maint.rect.width
        day_box_h = 36
        day_box = pygame.Rect(day_box_x, day_box_y, day_box_w, day_box_h)
        pygame.draw.rect(screen, (5, 5, 5), day_box, border_radius=3)
        pygame.draw.rect(screen, DIM_GREEN, day_box, 1, border_radius=3)

        # Status de ativacao
        pre_activation = gm.elapsed_time < gm.ACTIVATION_DELAY
        if pre_activation:
            remaining = int(gm.ACTIVATION_DELAY - gm.elapsed_time)
            mins = remaining // 60
            secs = remaining % 60
            day_text = f"[* {day_mgr.day_name} -- TUDO CALMO]"
            time_text = f"PRIMEIRA ANOMALIA EM: {mins:02d}:{secs:02d}"
            label_color = OFF_GREEN
        else:
            day_text = f"[* {day_mgr.day_name}]"
            time_text = f"RELOGIO: {day_mgr.get_display_time()}"
            label_color = GREEN

        day_label = font_title.render(day_text, True, label_color)
        screen.blit(day_label, (day_box_x + 12, day_box_y + 4))

        day_time_label = font_small.render(time_text, True, MED_GREEN)
        screen.blit(day_time_label, (day_box_x + 12, day_box_y + 21))

        # -- Barra de sanidade --
        sanity_y = day_box_y + day_box_h + 10 + oy
        sanity_x = maint_x + ox

        san_label = font_small.render("SANIDADE MENTAL", True, MED_GREEN)
        screen.blit(san_label, (sanity_x, sanity_y))

        bar_x, bar_y, bar_w, bar_h = sanity_x, sanity_y + 18, radio_w, 16
        pygame.draw.rect(screen, (15, 15, 15),
                         (bar_x, bar_y, bar_w, bar_h), border_radius=2)

        fill_w = int(bar_w * gm.sanity)
        if gm.sanity > 0.6:
            bar_color = GREEN
        elif gm.sanity > 0.3:
            bar_color = (200, 180, 0)
        else:
            bar_color = WARN_RED

        if fill_w > 0:
            pygame.draw.rect(screen, bar_color,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=2)

        # -- Barra de resistencia da capsula --
        capsule_y = sanity_y + 40
        capsule_label = font_small.render("INTEGRIDADE DA CAPSULA", True, MED_GREEN)
        screen.blit(capsule_label, (sanity_x, capsule_y))

        capsule_bar_x = sanity_x
        capsule_bar_y = capsule_y + 18
        capsule_bar_w = radio_w
        capsule_bar_h = 16
        pygame.draw.rect(screen, (15, 15, 15),
                         (capsule_bar_x, capsule_bar_y, capsule_bar_w, capsule_bar_h),
                         border_radius=2)

        capsule_fill = int(capsule_bar_w * gm.capsule_resistance)
        if gm.capsule_resistance > 0.6:
            capsule_color = (0, 140, 200)  # Azul ciano
        elif gm.capsule_resistance > 0.3:
            capsule_color = (200, 180, 0)  # Amarelo
        else:
            capsule_color = WARN_RED  # Vermelho

        if capsule_fill > 0:
            pygame.draw.rect(screen, capsule_color,
                             (capsule_bar_x, capsule_bar_y, capsule_fill, capsule_bar_h),
                             border_radius=2)

        # -- Status --
        if gm.sanity > 0.3:
            status_text = "STATUS: OPERACIONAL"
            status_color = MED_GREEN
        else:
            status_text = "STATUS: COMPROMETIDO"
            status_color = WARN_RED

        status_surf = font_status.render(status_text, True, status_color)
        screen.blit(status_surf, (info_x, info_y + 52))

        # -- Efeitos CRT --
        draw_scanlines(screen)

        sanity_val = gm.sanity
        vignette_intensity = 0.15 + (1.0 - sanity_val) * 0.5
        draw_vignette(screen, vignette_intensity)

        if sanity_val < 0.7:
            grain_amount = int(50 + (1.0 - sanity_val) * 150)
            draw_film_grain(screen, grain_amount)

        # -- Dessaturacao sutil quando sanidade baixa --
        if sanity_val < 0.5:
            darkness = int((0.5 - sanity_val) * 50)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, darkness))
            screen.blit(overlay, (0, 0))

        # -- Flip --
        # Transicao de dia (por cima de tudo)
        day_mgr.draw_transition(screen)

        # Game over screen
        if gm.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            font_go = pygame.font.SysFont("monospace", 36, bold=True)
            font_go_msg = pygame.font.SysFont("monospace", 16)

            go_text = font_go.render("SINAL PERDIDO", True, WARN_RED)
            go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            screen.blit(go_text, go_rect)

            go_msg = font_go_msg.render(gm.game_over_reason, True, (180, 120, 120))
            msg_rect = go_msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            screen.blit(go_msg, msg_rect)

            pygame.display.flip()
            pygame.time.wait(5000)
            running = False
            break

        pygame.display.flip()

        # Game over -- fim dos 7 dias
        if day_mgr.is_game_over:
            pygame.time.wait(3000)
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
