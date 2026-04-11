"""DayManager -- Ciclo de 7 dias, 8 minutos cada."""

import pygame


class DayManager:
    """Gerencia o ciclo de 7 dias do jogo.

    Cada dia dura 8 minutos (480 segundos) na vida real.
    Total do jogo: 56 minutos.
    """

    TOTAL_DAYS = 7
    SECONDS_PER_DAY = 8 * 60  # 480 segundos = 8 minutos

    DAY_NAMES = [
        "SEGUNDA-FEIRA",
        "TERCA-FEIRA",
        "QUARTA-FEIRA",
        "QUINTA-FEIRA",
        "SEXTA-FEIRA",
        "SABADO",
        "DOMINGO",
    ]

    DAY_MESSAGES = {
        0: "Dia 1. O turno comecou.",
        1: "Dia 2. Algo mudou la fora.",
        2: "Dia 3. As leituras sao inconsistentes.",
        3: "Dia 4. O zelador anterior passou por aqui.",
        4: "Dia 5. As entidades estao mais proximas.",
        5: "Dia 6. A sala parece menor.",
        6: "Dia 7. Ultimo dia. Sobreviva ate o fim.",
    }

    def __init__(self, gm):
        self.gm = gm
        self.current_day = 0          # 0-6
        self.day_timer = 0.0          # Segundos acumulados no dia atual

        # Transicao
        self.is_transitioning = False
        self.transition_timer = 0.0
        self.transition_duration = 3.0  # Duracao do fade entre dias
        self.transition_message = ""

        # Callback para when o dia muda
        self.on_day_change = None

    @property
    def day_progress(self) -> float:
        """Progresso do dia atual (0.0 a 1.0)."""
        return self.day_timer / self.SECONDS_PER_DAY

    @property
    def day_time_remaining(self) -> int:
        """Segundos restantes no dia atual."""
        return max(0, int(self.SECONDS_PER_DAY - self.day_timer))

    @property
    def day_name(self) -> str:
        """Nome do dia atual."""
        return self.DAY_NAMES[self.current_day]

    @property
    def day_number(self) -> int:
        """Numero do dia (1-7)."""
        return self.current_day + 1

    @property
    def is_last_day(self) -> bool:
        return self.current_day == self.TOTAL_DAYS - 1

    @property
    def is_game_over(self) -> bool:
        """Jogo acabou -- passou do dia 7."""
        return self.current_day >= self.TOTAL_DAYS

    def update(self, dt: float):
        """Atualiza o temporizador do dia."""
        if self.is_game_over:
            return

        # Em transicao -- apenas contar o timer
        if self.is_transitioning:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.is_transitioning = False
                self._advance_day()
            return

        self.day_timer += dt

        # Dia terminou -- iniciar transicao
        if self.day_timer >= self.SECONDS_PER_DAY:
            self._start_transition()

    def _start_transition(self):
        """Inicia a transicao para o proximo dia."""
        self.is_transitioning = True
        self.transition_timer = self.transition_duration

        next_day = self.current_day + 1
        if next_day < self.TOTAL_DAYS:
            self.transition_message = self.DAY_MESSAGES.get(next_day, "")
        else:
            self.transition_message = "O turno acabou."

        if self.on_day_change:
            self.on_day_change(self.current_day + 1)

    def _advance_day(self):
        """Avanca para o proximo dia."""
        self.current_day += 1
        self.day_timer = 0.0
        self.transition_message = ""

        # Escalar dificuldade com o dia
        self._apply_day_difficulty()

    def _apply_day_difficulty(self):
        """Ajusta parametros do jogo baseado no dia atual."""
        day_factor = self.current_day / self.TOTAL_DAYS  # 0.0 a 1.0

        # Feature 1: estacoes trocam mais rapido nos dias finais
        self.gm.SLOWDOWN_RATE = 0.003 + day_factor * 0.005

        # Feature 2: ameaca base sobe com o dia (mais suave)
        self.gm.entity_threat = max(
            self.gm.entity_threat,
            day_factor * 0.2
        )

        # Tolerancia do radio: valores fixos por dia (nao cumulativo)
        # Dia 1: 0.50, Dia 7: ~0.32
        self.gm.RADIO_TOLERANCE_BASE = max(
            0.32,
            0.50 - day_factor * 0.18
        )

        # Intervalo de troca base: valores fixos por dia
        # Dia 1: 25s, Dia 7: ~17s
        self.gm.STATION_CHANGE_INTERVAL_BASE = max(
            17.0,
            25.0 - day_factor * 8.0
        )

    def get_display_time(self) -> str:
        """Retorna string formatada como um horario de relogio (ex: 06:00 -> 14:00).

        Cada dia = 8 horas simuladas. O turno comeca as 06:00 e termina as 14:00.
        """
        # Progresso do dia (0.0 a 1.0)
        progress = self.day_progress

        # Cada dia = 8 horas (480 minutos), comecando as 06:00
        start_hour = 6
        total_day_minutes = 8 * 60  # 480 minutos por dia
        current_day_minutes = int(progress * total_day_minutes)

        total_minutes = start_hour * 60 + current_day_minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return f"{hours:02d}:{minutes:02d}"

    def draw_transition(self, surface: pygame.Surface):
        """Desenha a tela de transicao entre dias."""
        if not self.is_transitioning:
            return

        w, h = surface.get_size()
        progress = 1.0 - (self.transition_timer / self.transition_duration)

        # Fade in/out
        if progress < 0.5:
            alpha = int((progress / 0.5) * 200)
        else:
            alpha = int(((1.0 - progress) / 0.5) * 200)

        # Fundo escuro
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))

        # Texto do dia
        if alpha > 50:
            font_day = pygame.font.SysFont("monospace", 28, bold=True)
            font_msg = pygame.font.SysFont("monospace", 14)

            day_label = f"DIA {self.current_day + 2}" if not self.is_last_day else "FIM DO TURNO"
            day_surf = font_day.render(day_label, True, (0, 255, 51, alpha))
            day_rect = day_surf.get_rect(center=(w // 2, h // 2 - 20))
            surface.blit(day_surf, day_rect)

            if self.transition_message:
                msg_surf = font_msg.render(self.transition_message, True, (102, 153, 77, alpha))
                msg_rect = msg_surf.get_rect(center=(w // 2, h // 2 + 20))
                surface.blit(msg_surf, msg_rect)
