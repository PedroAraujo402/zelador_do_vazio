"""SanityManager -- Efeitos visuais baseados na sanidade."""

import math
import random


class SanityManager:
    """Controla shake de camera e intensidade de efeitos."""

    def __init__(self, gm):
        self.gm = gm

        # -- Shake --
        self.shake_intensity_max = 8.0
        self.shake_frequency = 15.0
        self.current_shake = 0.0
        self.shake_offset = (0, 0)

        # -- Panic attacks --
        self.panic_threshold = 0.3
        self.panic_timer = 0.0
        self.panic_min_interval = 20.0
        self.in_panic = False

        # -- Tempo interno --
        self._time = 0.0

    def update(self, dt: float):
        self._time += dt

        # Shake
        target = self.shake_intensity_max * (1.0 - self.gm.sanity)
        self.current_shake += (target - self.current_shake) * dt * 4.0

        if self.current_shake > 0.5:
            sx = self._noise(self._time * self.shake_frequency) * self.current_shake
            sy = self._noise(self._time * self.shake_frequency * 1.3 + 1.0) * self.current_shake * 0.7
            self.shake_offset = (int(sx), int(sy))
        else:
            self.shake_offset = (0, 0)

        # Panic attacks
        self.panic_timer -= dt
        if self.panic_timer <= 0 and self.gm.sanity < self.panic_threshold:
            if random.random() < 0.02:
                self._start_panic()

    def _noise(self, t: float) -> float:
        return math.sin(t) * 0.5 + math.sin(t * 2.7) * 0.3 + math.sin(t * 5.1) * 0.2

    def _start_panic(self):
        self.in_panic = True
        self.panic_timer = self.panic_min_interval
        self.current_shake = self.shake_intensity_max * 1.5
        self.gm.trigger_panic(0.08)
