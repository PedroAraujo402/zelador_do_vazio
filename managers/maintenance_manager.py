"""MaintenanceManager -- Botoes de manutencao que falham e precisam de reparo."""

import pygame
import random


class MaintenanceButton:
    """Um botao de sistema que ocasionalmente entra em erro e precisa ser segurado para consertar."""

    # Estados
    OK = "ok"
    ERROR = "error"
    REPAIRING = "repairing"

    def __init__(self, x: int, y: int, width: int, height: int, label: str, icon: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.icon = icon
        self.state = self.OK

        # Tempo de reparo: quanto segurar para consertar (segundos)
        self.repair_time_required = 2.0
        self.repair_progress = 0.0  # 0.0 a 1.0

        # Cooldown entre erros (segundos)
        self.error_cooldown = 0.0
        self.error_cooldown_min = 15.0
        self.error_cooldown_max = 40.0

        # Visual
        self.font_label = pygame.font.SysFont("monospace", 11, bold=True)
        self.font_status = pygame.font.SysFont("monospace", 9)

        # Cores
        self.COLOR_OK = (0, 180, 60)
        self.COLOR_OK_BG = (0, 30, 10)
        self.COLOR_ERROR = (200, 40, 40)
        self.COLOR_ERROR_BG = (40, 8, 8)
        self.COLOR_REPAIR = (200, 180, 0)
        self.COLOR_REPAIR_BG = (40, 35, 8)
        self.COLOR_BORDER_OK = (0, 255, 80)
        self.COLOR_BORDER_ERROR = (255, 60, 60)
        self.COLOR_BORDER_REPAIR = (255, 230, 0)

    def update(self, dt: float, threat_level: float):
        """Atualiza estado do botao."""
        # Cooldown de erro
        if self.state == self.OK:
            self.error_cooldown -= dt
            if self.error_cooldown <= 0:
                # Chance de erro baseada na ameaca
                error_chance = 0.005 + threat_level * 0.02
                if random.random() < error_chance:
                    self.state = self.ERROR
                    self.error_cooldown = random.uniform(
                        self.error_cooldown_min,
                        self.error_cooldown_max
                    )

        # Reparando
        elif self.state == self.REPAIRING:
            self.repair_progress += dt / self.repair_time_required
            if self.repair_progress >= 1.0:
                # Consertado!
                self.state = self.OK
                self.repair_progress = 0.0
                self.error_cooldown = random.uniform(
                    self.error_cooldown_min * 0.5,
                    self.error_cooldown_max * 0.8
                )

    def start_repair(self) -> bool:
        """Inicia reparo se estiver em erro. Retorna True se conseguiu."""
        if self.state == self.ERROR:
            self.state = self.REPAIRING
            self.repair_progress = 0.0
            return True
        return False

    def stop_repair(self):
        """Para de segurar -- progresso congela (nao reseta)."""
        if self.state == self.REPAIRING:
            # Se parar de segregar, mantem o progresso acumulado
            pass

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Processa eventos. Retorna True se interagiu."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.state == self.ERROR:
                    return self.start_repair()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.state == self.REPAIRING:
                self.stop_repair()
        return False

    def draw(self, surface: pygame.Surface):
        """Desenha o botao no estado atual."""
        if self.state == self.OK:
            bg_color = self.COLOR_OK_BG
            border_color = self.COLOR_BORDER_OK
            text_color = self.COLOR_OK
            status_text = "OPERACIONAL"
            status_color = self.COLOR_OK
        elif self.state == self.ERROR:
            bg_color = self.COLOR_ERROR_BG
            border_color = self.COLOR_BORDER_ERROR
            text_color = self.COLOR_ERROR
            status_text = "[!] FALHA -- SEGURE PARA REPARAR"
            status_color = self.COLOR_ERROR
        else:  # REPAIRING
            bg_color = self.COLOR_REPAIR_BG
            border_color = self.COLOR_BORDER_REPAIR
            text_color = self.COLOR_REPAIR
            status_text = f"REPARANDO... {int(self.repair_progress * 100)}%"
            status_color = self.COLOR_REPAIR

        # Fundo
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=3)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=3)

        # Icone + label
        icon_surf = self.font_label.render(self.icon, True, text_color)
        label_surf = self.font_label.render(self.label, True, text_color)

        surface.blit(icon_surf, (self.rect.x + 10, self.rect.y + 8))
        surface.blit(label_surf, (self.rect.x + 30, self.rect.y + 8))

        # Status
        status_surf = self.font_status.render(status_text, True, status_color)
        surface.blit(status_surf, (self.rect.x + 10, self.rect.y + 30))

        # Barra de progresso (so quando reparando)
        if self.state == self.REPAIRING:
            bar_x = self.rect.x + 10
            bar_y = self.rect.y + self.rect.height - 14
            bar_w = self.rect.width - 20
            bar_h = 8

            pygame.draw.rect(surface, (20, 20, 20),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=2)

            fill_w = int(bar_w * self.repair_progress)
            if fill_w > 0:
                pygame.draw.rect(surface, self.COLOR_REPAIR,
                                 (bar_x, bar_y, fill_w, bar_h), border_radius=2)


class MaintenanceManager:
    """Gerencia os 3 botoes de manutencao do painel."""

    def __init__(self, x: int, y: int, width: int, gm):
        self.gm = gm
        self.rect = pygame.Rect(x, y, width, 170)

        # Botao tamanho e espacamento
        btn_w = width - 20  # margem interna
        btn_h = 42
        gap = 8
        start_x = x + 10
        start_y = y + 22

        # 3 botoes de sistema
        self.buttons = [
            MaintenanceButton(start_x, start_y, btn_w, btn_h, "VENTILACAO", "[V]"),
            MaintenanceButton(start_x, start_y + btn_h + gap, btn_w, btn_h, "REFRIGERACAO", "[R]"),
            MaintenanceButton(start_x, start_y + (btn_h + gap) * 2, btn_w, btn_h, "ENERGIA", "[E]"),
        ]

        # Fontes
        self.font_title = pygame.font.SysFont("monospace", 14, bold=True)

        # Cores
        self.GREEN = (0, 255, 51)
        self.DIM_GREEN = (0, 90, 13)
        self.WARN_RED = (180, 40, 40)

    @property
    def faulty_count(self) -> int:
        """Quantos botoes estao com falha ou sendo reparados."""
        return sum(
            1 for b in self.buttons
            if b.state in (MaintenanceButton.ERROR, MaintenanceButton.REPAIRING)
        )

    def update(self, dt: float):
        """Atualiza todos os botoes."""
        # Nada acontece antes do delay de ativacao
        if self.gm.elapsed_time < self.gm.ACTIVATION_DELAY:
            return

        threat = self.gm.entity_threat
        for btn in self.buttons:
            btn.update(dt, threat)

        # Penalidade: botoes com falha aumentam ameaca
        if self.faulty_count > 0:
            self.gm.entity_threat = min(
                1.0,
                self.gm.entity_threat + self.faulty_count * 0.001 * dt * 60.0
            )

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Processa eventos para todos os botoes."""
        any_interaction = False
        for btn in self.buttons:
            if btn.handle_event(event):
                any_interaction = True
        return any_interaction

    def draw(self, surface: pygame.Surface, ox: int = 0, oy: int = 0):
        """Desenha o painel de manutencao."""
        r = self.rect.move(ox, oy)

        # Fundo do painel
        pygame.draw.rect(surface, (6, 6, 6), r, border_radius=4)
        pygame.draw.rect(surface, self.DIM_GREEN, r, 1, border_radius=4)

        # Titulo
        title = self.font_title.render("[ SISTEMAS DA SALA ]", True, self.GREEN)
        surface.blit(title, (r.x + 10, r.y + 6))

        # Botoes
        for btn in self.buttons:
            btn.draw(surface)
