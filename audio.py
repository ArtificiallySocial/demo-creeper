import time
from typing import Dict, Optional

import pygame

import config


class AudioManager:
    PRIORITY = {
        "HUMAN_DETECTED": 1,
        "TARGET_ACQUIRED": 2,
        "ALERT": 3,
    }

    def __init__(self):
        pygame.mixer.init()
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._last_played: Dict[str, float] = {}
        self._current_priority: int = 0

        for event_name in self.PRIORITY.keys():
            path = f"{config.ASSET_DIR}/{event_name.lower()}.mp3"
            self._sounds[event_name] = pygame.mixer.Sound(path)
            self._last_played[event_name] = 0

        self._sounds["startup"] = pygame.mixer.Sound(f"{config.ASSET_DIR}/startup.mp3")
        pygame.time.delay(2000)
        self._sounds["startup"].play()

    def trigger(self, event: str) -> None:
        now = time.time()
        if now - self._last_played[event] < config.AUDIO_COOLDOWN_SECONDS:
            return

        priority = self.PRIORITY.get(event, 0)
        if priority < self._current_priority:
            return
        if self._sounds[event].get_num_channels() > 0:
            return
        if priority > self._current_priority:
            pygame.mixer.stop()

        self._sounds[event].play()
        self._last_played[event] = now
        self._current_priority = priority

    def stop_all(self) -> None:
        pygame.mixer.stop()

    def reset_priority(self) -> None:
        self._current_priority = 0
