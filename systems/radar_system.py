"""RadarSystem -- Radar de varredura vetorial estilo sonar."""

import pygame
import math
import random


class RadarEntity:
    """Uma unica criatura no radar -- posicao persistente que drift ao centro."""

    # 1 hora de jogo em segundos reais (8h de jogo = 480s reais -> 60s por hora)
    SECONDS_PER_HOUR = 60.0
    HOUR_BEFORE_APPEAR_DAY1 = 2  # Dia 1: ganha AP a partir da 2a hora

    def __init__(self, position: tuple, starting_ap: int = 0):
        self.position = list(position)       # [x, y] normalizado (-1 a 1), mutavel
        self.lifetime = 99999.0              # Persistente
        self.age = 0.0
        self.drift_speed = random.uniform(0.015, 0.035)
        self.wobble = random.uniform(0, math.tau)
        self.alive = True
        self.respawn_timer = 0.0             # Tempo antes de reaparecer em outro lugar

        # -- Sistema de pontos de acao (invisivel ao jogador) --
        self.starting_ap = starting_ap       # AP base herdado do dia anterior
        self.hour_timer = 0.0                # Acumula tempo da hora atual
        self.action_points = starting_ap     # AP disponiveis esta hora
        self.can_move_this_hour = False      # Resultado da rolagem oculta
        self.has_rolled_this_hour = False

    def _roll_action_check(self) -> bool:
        """d20 silencioso: se rolou <= AP, a criatura pode se mover."""
        if self.action_points <= 0:
            return False
        roll = random.randint(1, 20)
        return roll <= self.action_points

    def tick_hour(self):
        """Chamado a cada hora de jogo -- recalcula AP e faz rolagem."""
        # Recalcula AP para esta hora
        self.action_points = self.starting_ap
        # AP acumula com as horas passadas desde a 3a hora
        hours_into_ap = self._hours_since_activation()
        self.action_points += max(0, hours_into_ap)

        # Rolagem oculta
        self.can_move_this_hour = self._roll_action_check()
        self.has_rolled_this_hour = True

    def _hours_since_activation(self) -> int:
        """Quantas horas se passaram desde a 3a hora (quando a criatura comeca a agir)."""
        # Sera calculado externamente e passado via update
        return 0

    def update_hour_tracking(self, hour_in_day: int, day_number: int = 1):
        """Atualiza o rastreamento de horas e dispara rolagem oculta quando muda a hora.

        Dia 1: hora 0 -> 0 AP, hora 1 -> 1 AP, hora 2 -> 2 AP... (2a hora = indice 1)
        Dia 2: hora 0 -> 1 AP, hora 1 -> 2 AP, hora 2 -> 3 AP...
        Dia 3: hora 0 -> 2 AP, hora 1 -> 3 AP, hora 2 -> 4 AP...
        """
        if day_number == 1:
            # Dia 1: comeca com 0 AP, ganha 1 AP a partir da 2a hora (indice 1)
            current_ap = max(0, hour_in_day)
        else:
            # Dia 2+: base = dia - 1, + 1 por hora
            current_ap = (day_number - 1) + hour_in_day

        if current_ap != self.action_points:
            self.action_points = current_ap
            self.can_move_this_hour = self._roll_action_check()

    def drift_toward_center(self, threat: float, dt: float, elapsed_time: float = 0.0):
        """Quanto maior a ameaca e o tempo de jogo, mais rapido vai ao centro."""
        if threat < 0.05:
            return

        # Se a rolagem falhou, a criatura fica parada esta hora
        if not self.can_move_this_hour:
            return

        # Aceleracao baseada no tempo de jogo: quanto mais tempo passa, mais rapido
        # Fator de aceleracao: 1.0 no inicio -> 3.0+ apos muito tempo
        time_acceleration = 1.0 + (elapsed_time / 120.0) * 2.0  # Triplica a cada 2 min

        speed = self.drift_speed * threat * time_acceleration * dt * 60.0

        self.position[0] *= (1.0 - speed)
        self.position[1] *= (1.0 - speed)

        self.wobble += dt * 3.0
        self.position[0] += math.sin(self.wobble) * 0.003 * threat
        self.position[1] += math.cos(self.wobble * 1.3) * 0.003 * threat

    def reposition(self, threat: float):
        """Teleporta a criatura para uma nova posicao na borda."""
        min_dist = max(0.3, 0.7 - threat * 0.3)
        max_dist = 0.95
        angle = random.uniform(0, math.tau)
        dist = random.uniform(min_dist, max_dist)
        self.position = [math.cos(angle) * dist, math.sin(angle) * dist]
        self.wobble = random.uniform(0, math.tau)

    @property
    def proximity(self):
        return math.sqrt(self.position[0] ** 2 + self.position[1] ** 2)


class RadarSystem:
    """Radar vetorial com sweep rotacional e UMA unica criatura persistente."""

    def __init__(self, x: int, y: int, size: int, gm, activation_time: float = 0.0, day_mgr=None):
        self.base_x = x
        self.base_y = y
        self.size = size
        self.gm = gm
        self.day_mgr = day_mgr
        self.activation_time = activation_time  # Segundos de jogo para ativar

        self.rect = pygame.Rect(x, y, size, size)
        self.radius = size // 2 - 10

        # Offset de shake
        self.draw_x = 0
        self.draw_y = 0

        # -- Sweep --
        self.sweep_angle = 0.0
        self.sweep_speed = 0.8  # rad/s

        # -- Criatura unica --
        self.creature = None  # RadarEntity single
        self.creature_active = False

        # -- Rastreamento de horas para sistema de AP --
        self.last_tracked_hour = -1  # Qual hora do dia ja foi processada
        self.seconds_into_day = 0.0  # Segundos reais dentro do dia atual
        self.last_day_number = 0     # Para detectar mudanca de dia
        self._last_sanity_tier = -1  # Tier de sanidade anterior (para detectar threshold)

        # -- Cores --
        self.GREEN = (0, 255, 51)
        self.DIM_GREEN = (0, 90, 13)
        self.MED_GREEN = (0, 140, 30)
        self.BLACK = (0, 0, 0)

        # -- Fontes --
        self.font_title = pygame.font.SysFont("monospace", 14, bold=True)

    def _sanity_multiplier(self, sanity: float) -> float:
        """Calcula o multiplicador de AP baseado na sanidade."""
        if sanity <= 0.0:
            return 4.0
        elif sanity < 0.25:
            return 3.0
        elif sanity < 0.50:
            return 2.0
        return 1.0

    def _get_sanity_tier(self, sanity: float) -> int:
        """Retorna o tier de sanidade (0-3) para deteccao de threshold."""
        if sanity <= 0.0:
            return 0
        elif sanity < 0.25:
            return 1
        elif sanity < 0.50:
            return 2
        return 3

    def update(self, dt: float):
        elapsed = self.gm.elapsed_time

        # Verificar se ja passou do tempo de ativacao
        if not self.creature_active and elapsed >= self.activation_time:
            self._spawn_creature()

        # Avancar sweep
        self.sweep_angle += self.sweep_speed * dt
        if self.sweep_angle > math.tau:
            self.sweep_angle -= math.tau

        if not self.creature_active or self.creature is None:
            return

        # -- Rastrear horas do dia para sistema de AP --
        if self.day_mgr is None:
            return  # Sem day_mgr, sem tracking de horas

        day_number = self.day_mgr.current_day + 1  # 1-7

        # Detectar mudanca de dia -- reset e recalcular starting AP
        if day_number != self.last_day_number:
            self.last_day_number = day_number
            self.seconds_into_day = 0.0
            self.last_tracked_hour = -1
            # AP base: dia 1 = 0, dia 2 = 1, dia 3 = 2...
            if self.creature:
                self.creature.starting_ap = day_number - 1
                self.creature.action_points = self.creature.starting_ap
                self.creature.can_move_this_hour = False
                self._last_sanity_tier = -1  # Reset tier tracking

        # Detectar cruzamento de threshold de sanidade -- refazer rolagem
        current_tier = self._get_sanity_tier(self.gm.sanity)
        if current_tier != self._last_sanity_tier:
            self._last_sanity_tier = current_tier
            if self.creature and self.creature.action_points > 0:
                mult = self._sanity_multiplier(self.gm.sanity)
                effective_ap = int(self.creature.action_points * mult)
                roll = random.randint(1, 20)
                self.creature.can_move_this_hour = roll <= effective_ap

        # Acumular tempo dentro do dia
        self.seconds_into_day += dt

        # Calcular hora atual do dia (0-7)
        current_hour = int(self.seconds_into_day / RadarEntity.SECONDS_PER_HOUR)
        current_hour = min(current_hour, 7)  # Cap em 7

        # Se mudou a hora, atualizar tracking da criatura
        if current_hour != self.last_tracked_hour:
            self.last_tracked_hour = current_hour
            if self.creature:
                self.creature.update_hour_tracking(current_hour, day_number)
                # Aplicar multiplicador de sanidade na rolagem
                if self.creature.action_points > 0:
                    mult = self._sanity_multiplier(self.gm.sanity)
                    effective_ap = int(self.creature.action_points * mult)
                    roll = random.randint(1, 20)
                    self.creature.can_move_this_hour = roll <= effective_ap
                    self._last_sanity_tier = self._get_sanity_tier(self.gm.sanity)

        threat = self.gm.entity_threat
        self.creature.drift_toward_center(threat, dt, elapsed)
        self.creature.age += dt

        # Se chegou muito perto do centro, reaparecer na borda
        if self.creature.proximity < 0.05:
            self.creature.reposition(threat)

        # Reaparecer periodicamente (a cada 20-40s) para dar sensacao de que "some e volta"
        self.creature.respawn_timer += dt
        respawn_interval = 25.0 - threat * 10.0  # 25s -> 15s
        if self.creature.respawn_timer >= respawn_interval:
            self.creature.respawn_timer = 0.0
            self.creature.reposition(threat)

        # Sanidade por proximidade
        if self.creature.proximity < 0.25:
            self.gm.trigger_panic(1.0 - self.creature.proximity)

        # Atualizar resistencia da capsula
        self.gm.update_capsule_resistance(dt, self.creature.proximity)

        # Chance de captura quando capsula esta fraca
        if self.gm.check_creature_capture():
            self.gm.game_over = True
            self.gm.game_over_reason = "A capsula cedeu. A criatura entrou."

    @property
    def creature_proximity(self) -> float:
        """Retorna a proximidade da criatura ao centro (0 = centro, 1 = borda)."""
        if self.creature is not None:
            return self.creature.proximity
        return 1.0

    def _spawn_creature(self):
        """Spawn a single creature at the edge of the radar."""
        angle = random.uniform(0, math.tau)
        dist = random.uniform(0.7, 0.95)
        pos = (math.cos(angle) * dist, math.sin(angle) * dist)
        self.creature = RadarEntity(pos)
        self.creature_active = True

    def draw(self, surface: pygame.Surface):
        # Calcular center com offset de shake
        cx = self.base_x + self.draw_x + self.size // 2
        cy = self.base_y + self.draw_y + self.size // 2
        center = (cx, cy)

        # Fundo preto circular
        pygame.draw.circle(surface, self.BLACK, center, self.radius)
        pygame.draw.circle(surface, self.DIM_GREEN, center, self.radius, 1)

        # Grid -- circulos concentricos
        rings = 4
        for i in range(1, rings + 1):
            r = (self.radius / rings) * i
            pygame.draw.circle(surface, self.DIM_GREEN, center, int(r), 1)

        # Grid -- linhas radiais (cruz)
        for i in range(4):
            angle = (math.tau / 4) * i
            end_x = cx + int(math.cos(angle) * self.radius)
            end_y = cy + int(math.sin(angle) * self.radius)
            pygame.draw.line(surface, self.DIM_GREEN, center, (end_x, end_y), 1)

        # Sweep trail (fatia translucida)
        for a_offset in [0, -0.1, -0.2, -0.3]:
            a = self.sweep_angle + a_offset
            alpha = int(40 * (1.0 - abs(a_offset) / 0.3))
            end_x = cx + int(math.cos(a) * self.radius)
            end_y = cy + int(math.sin(a) * self.radius)
            g_val = int(255 * (1.0 - abs(a_offset) / 0.3))
            trail_color = (0, g_val, 20, alpha)
            pygame.draw.line(surface, trail_color, center, (end_x, end_y), 2)

        # Linha do sweep
        sweep_end_x = cx + int(math.cos(self.sweep_angle) * self.radius)
        sweep_end_y = cy + int(math.sin(self.sweep_angle) * self.radius)
        pygame.draw.line(surface, self.GREEN, center, (sweep_end_x, sweep_end_y), 2)

        # Criatura unica
        if self.creature_active and self.creature is not None:
            ent = self.creature
            screen_x = cx + int(ent.position[0] * self.radius)
            screen_y = cy + int(ent.position[1] * self.radius)

            ent_angle = math.atan2(ent.position[1], ent.position[0])
            angle_diff = abs(((self.sweep_angle - ent_angle + math.pi) % math.tau) - math.pi)

            if angle_diff < 0.15:
                # Sweep acabou de passar -- brilho forte
                pygame.draw.circle(surface, (0, 60, 15), (screen_x, screen_y), 12)
                pygame.draw.circle(surface, self.GREEN, (screen_x, screen_y), 7)
            else:
                # Fade sutil quando o sweep nao passa
                pygame.draw.circle(surface, (0, 120, 30), (screen_x, screen_y), 4)

        # Centro (jogador)
        pygame.draw.circle(surface, self.GREEN, center, 3)
        pygame.draw.circle(surface, (0, 60, 15), center, 7)

    def get_rect(self) -> pygame.Rect:
        return self.rect
