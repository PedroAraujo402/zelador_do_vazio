"""GameManager -- Estado global do jogo."""

import random
import math


class GameManager:
    """Singleton que gerencia estado global: sanidade, frequencia, mensagens, tempo."""

    # -- Instancia singleton --
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -- Configuracoes base --
    RADIO_TOLERANCE_BASE = 0.5         # Tolerancia inicial de sintonia
    RADIO_TOLERANCE_MIN = 0.15         # Tolerancia minima (mais dificil)
    SANITY_LOSS_RADIO_DESYNC = 0.0008  # Perda por estar fora de sintonia
    SANITY_LOSS_RADAR_PROXIMITY = 0.001
    SANITY_GAIN_WHEN_TUNED = 0.0012   # Ganho por estar sintonizado (maior que perda)

    # -- Feature 1: troca de estacao --
    STATION_CHANGE_INTERVAL_BASE = 25.0   # Segundos para estacao mudar (inicio)
    STATION_CHANGE_INTERVAL_MIN = 12.0    # Minimo que pode chegar

    # -- Feature 3: velocidade de troca diminui com tempo --
    SLOWDOWN_RATE = 0.003  # Quantos segundos extra por segundo de jogo

    # -- Delay de ativacao: 3h game = 3/6 do dia = 0.5 * 480s = 120s real
    ACTIVATION_DELAY = 120.0  # Segundos reais para tudo comecar

    RADIO_MESSAGES = [
        "Voce nao esta sozinho.",
        "Nao olhe para fora.",
        "O vacuo observa.",
        "Mantenha a frequencia.",
        "Eles sabem que voce esta aqui.",
        "Desligue o radar.",
        "...ajuda... ninguem... vem...",
        "O zelador anterior... ele ainda esta aqui.",
    ]

    def __init__(self):
        # -- Estado --
        self.sanity: float = 1.0
        self.current_frequency: float = 87.5
        self.target_frequency: float = 0.0
        self.radio_tuned: bool = False

        # Tempo de jogo
        self.elapsed_time: float = 0.0  # Segundos totais
        self.low_sanity_time: float = 0.0  # Tempo acumulado com sanidade < 0.5

        # Grace period apos troca de estacao
        self.station_change_grace: float = 0.0  # Segundos de protecao apos troca
        self.STATION_GRACE_DURATION = 3.0  # 3 segundos sem perder sanidade

        # Troca de estacao
        self._station_change_timer: float = 0.0

        # Mensagem ativa
        self.active_message: str = ""
        self.message_timer: float = 0.0
        self.message_display_time: float = 0.0
        self.message_visible: bool = False

        # Nivel de ameaca das entidades (0 = normal, 1 = maximo)
        self.entity_threat: float = 0.0

        # Resistencia da capsula (1.0 = intacta, 0.0 = rompida = game over)
        self.capsule_resistance: float = 1.0
        self.CAPSULE_DAMAGE_RATE = 0.015    # Dano por frame quando criatura esta perto
        self.CAPSULE_REGEN_RATE = 0.0003    # Regeneracao muito lenta quando segura

        # Game over
        self.game_over: bool = False
        self.game_over_reason: str = ""

        self._pick_new_target()

    # -- Propriedades calculadas --
    @property
    def radio_tolerance(self) -> float:
        """Tolerancia de sintonia diminui com a ameaca das entidades."""
        return max(
            self.RADIO_TOLERANCE_MIN,
            self.RADIO_TOLERANCE_BASE - self.entity_threat * 0.35
        )

    @property
    def station_change_interval(self) -> float:
        """Intervalo entre trocas: comeca rapido, fica mais lento com o tempo."""
        slowdown = self.elapsed_time * self.SLOWDOWN_RATE
        return max(
            self.STATION_CHANGE_INTERVAL_MIN,
            self.STATION_CHANGE_INTERVAL_BASE + slowdown
        )

    # -- Frequencia --
    def adjust_frequency(self, delta: float, sensitivity: float = 0.05):
        self.current_frequency = max(87.5, min(108.0, self.current_frequency + delta * sensitivity))

    def check_radio_tuned(self) -> bool:
        self.radio_tuned = abs(self.current_frequency - self.target_frequency) < self.radio_tolerance
        return self.radio_tuned

    def _pick_new_target(self):
        self.target_frequency = random.uniform(88.0, 107.5)
        # Dar um grace period: se a frequencia atual estiver perto do novo alvo,
        # considera sintonizado por um momento para nao punir instantaneamente
        self.radio_tuned = abs(self.current_frequency - self.target_frequency) < self.radio_tolerance

    def pick_new_target(self):
        self._pick_new_target()

    # -- Sanidade --
    def update_sanity(self, dt: float):
        # Nada acontece antes do delay de ativacao
        if self.elapsed_time < self.ACTIVATION_DELAY:
            return

        # Decrementar grace period
        if self.station_change_grace > 0:
            self.station_change_grace -= dt

        freq_diff = abs(self.current_frequency - self.target_frequency)

        # Durante o grace period, nao perder sanidade -- apenas ganhar se sintonizado
        if self.station_change_grace > 0:
            if self.radio_tuned:
                self.sanity += self.SANITY_GAIN_WHEN_TUNED * dt * 60.0
        elif freq_diff > self.radio_tolerance:
            self.sanity -= self.SANITY_LOSS_RADIO_DESYNC * dt * 60.0
        elif self.radio_tuned:
            self.sanity += self.SANITY_GAIN_WHEN_TUNED * dt * 60.0

        self.sanity = max(0.0, min(1.0, self.sanity))

        # Feature 2: acumular tempo com sanidade baixa -> entidades se aproximam
        if self.sanity < 0.5:
            self.low_sanity_time += dt * (1.0 - self.sanity * 2.0)  # Quanto menor, mais rapido acumula
            self.entity_threat = min(1.0, self.low_sanity_time / 60.0)  # 60s de sanidade baixa = ameaca maxima
        else:
            # Recuperacao lenta da ameaca
            self.low_sanity_time = max(0.0, self.low_sanity_time - dt * 0.3)
            self.entity_threat = min(1.0, self.low_sanity_time / 60.0)

    def trigger_panic(self, intensity: float):
        self.sanity -= intensity * 0.1
        self.sanity = max(0.0, self.sanity)

    # -- Resistencia da capsula --
    def update_capsule_resistance(self, dt: float, creature_proximity: float = 1.0):
        """Atualiza resistencia baseado na proximidade da criatura."""
        if self.elapsed_time < self.ACTIVATION_DELAY:
            return

        # Se a criatura esta perto (proximidade < 0.3 = dentro da zona de perigo)
        if creature_proximity < 0.3:
            # Dano proporcional a proximidade
            damage_factor = 1.0 - (creature_proximity / 0.3)  # 0 a 1
            self.capsule_resistance -= self.CAPSULE_DAMAGE_RATE * damage_factor * dt * 60.0
        else:
            # Regeneracao lenta quando a criatura esta longe
            self.capsule_resistance += self.CAPSULE_REGEN_RATE * dt * 60.0

        self.capsule_resistance = max(0.0, min(1.0, self.capsule_resistance))

        # Game over: resistencia zerada -> criatura pega o jogador
        if self.capsule_resistance <= 0.0 and not self.game_over:
            self.game_over = True
            self.game_over_reason = "A capsula foi comprometida. A criatura entrou."

    def check_creature_capture(self) -> bool:
        """Chance da criatura pegar o jogador quando a capsula esta fraca."""
        if self.capsule_resistance <= 0.0:
            return True
        # Chance escalar: 0% em 1.0 -> 5% em 0.3 -> 30% em 0.1
        if self.capsule_resistance < 0.3:
            chance = (0.3 - self.capsule_resistance) / 0.3 * 0.3
            return random.random() < chance
        return False

    # -- Troca de estacao (Feature 1 + 3) --
    def update_station_change(self, dt: float):
        self.elapsed_time += dt

        # Nada acontece antes do delay de ativacao
        if self.elapsed_time < self.ACTIVATION_DELAY:
            self._station_change_timer = 0.0
            return

        self._station_change_timer += dt

        interval = self.station_change_interval

        if self._station_change_timer >= interval:
            self._station_change_timer = 0.0
            self._pick_new_target()
            self.station_change_grace = self.STATION_GRACE_DURATION

    # -- Mensagens --
    def try_show_message(self, dt: float):
        if self.message_visible:
            self.message_display_time -= dt
            if self.message_display_time <= 0:
                self.message_visible = False
            return

        # Cooldown aleatorio entre 8-25s
        self.message_timer -= dt
        if self.message_timer <= 0 and self.radio_tuned:
            self.active_message = random.choice(self.RADIO_MESSAGES)
            self.message_visible = True
            self.message_display_time = 4.0
            self.message_timer = random.uniform(8.0, 25.0)
