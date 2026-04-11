"""RadioSystem -- Mecanica de sintonia de radio."""

import pygame


class RadioSystem:
    """Lida com interacao de sintonia, feedback visual e sons."""

    def __init__(self, x: int, y: int, width: int, height: int, gm):
        self.base_rect = pygame.Rect(x, y, width, height)
        self.gm = gm

        # Offset de shake
        self.draw_offset_x = 0
        self.draw_offset_y = 0

        # -- Estado de input --
        self.is_dragging: bool = False
        self.last_mouse_x: int = 0
        self.sensitivity: float = 0.05

        # -- Fontes --
        self.font_title = pygame.font.SysFont("monospace", 14, bold=True)
        self.font_freq = pygame.font.SysFont("monospace", 36, bold=True)
        self.font_status = pygame.font.SysFont("monospace", 14)
        self.font_knob = pygame.font.SysFont("monospace", 12)
        self.font_message = pygame.font.SysFont("monospace", 16)

        # -- Cores --
        self.GREEN = (0, 255, 51)
        self.DIM_GREEN = (0, 90, 13)
        self.MED_GREEN = (102, 153, 77)
        self.OFF_GREEN = (51, 77, 38)
        self.BLACK = (0, 0, 0)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Processa eventos de input. Retorna True se interagiu."""
        # Rect atual com offset
        r = self.base_rect.move(self.draw_offset_x, self.draw_offset_y)
        self.rect = r  # atualizar para draw

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if r.collidepoint(event.pos):
                self.is_dragging = True
                self.last_mouse_x = event.pos[0]
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            delta_x = event.pos[0] - self.last_mouse_x
            self.last_mouse_x = event.pos[0]
            self.gm.adjust_frequency(delta_x, self.sensitivity)
            return True
        return False

    def draw(self, surface: pygame.Surface):
        ox = self.draw_offset_x
        oy = self.draw_offset_y
        r = self.base_rect.move(ox, oy)

        # Fundo do painel de radio
        pygame.draw.rect(surface, (5, 5, 5), r, border_radius=4)
        pygame.draw.rect(surface, self.DIM_GREEN, r, 1, border_radius=4)

        cx = r.x + 15
        cy = r.y + 10

        # Titulo
        title_surf = self.font_title.render("[ RADIO -- SINTONIA MANUAL ]", True, self.GREEN)
        surface.blit(title_surf, (cx, cy))
        cy += 28

        # Frequencia
        if self.gm.elapsed_time < self.gm.ACTIVATION_DELAY:
            freq_text = "-- SEM SINAL --"
        else:
            freq_text = f"{self.gm.current_frequency:.1f} MHz"
        freq_surf = self.font_freq.render(freq_text, True, self.GREEN)
        surface.blit(freq_surf, (cx, cy))
        cy += 44

        # Status
        if self.gm.elapsed_time < self.gm.ACTIVATION_DELAY:
            status_text = "SISTEMAS NOMINAIS"
            status_color = self.DIM_GREEN
        elif self.gm.radio_tuned:
            status_text = "* SINTONIZADO"
            status_color = self.GREEN
        else:
            status_text = "- ESTATICA"
            status_color = self.OFF_GREEN

        status_surf = self.font_status.render(status_text, True, status_color)
        surface.blit(status_surf, (cx, cy))
        cy += 30

        # Area do knob
        knob_rect = pygame.Rect(cx, cy, r.width - 30, 50)
        pygame.draw.rect(surface, (10, 10, 10), knob_rect, border_radius=2)
        pygame.draw.rect(surface, self.DIM_GREEN, knob_rect, 1, border_radius=2)

        knob_text = "<--- ARRASTE PARA SINTONIZAR --->"
        knob_surf = self.font_knob.render(knob_text, True, self.OFF_GREEN)
        kx = cx + (knob_rect.width - knob_surf.get_width()) // 2
        ky = cy + (knob_rect.height - knob_surf.get_height()) // 2
        surface.blit(knob_surf, (kx, ky))
        cy += 58

        # Mensagem de radio
        if self.gm.message_visible and self.gm.active_message:
            msg_surf = self.font_message.render(self.gm.active_message, True, self.GREEN)
            surface.blit(msg_surf, (cx, cy))
