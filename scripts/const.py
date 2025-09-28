from pathlib import Path
from dataclasses import dataclass

import pygame

@dataclass
class Colors:
    background = pygame.Color("#151515")
    bar_bright = pygame.Color("#CCCCCC")
    bar_dim = pygame.Color("#747474")
    bar_dark = pygame.Color("#222222")
    wave = pygame.Color("#888888")

@dataclass
class Paths:
    images = Path("./tmp/images")
    tmp_audio = Path("./tmp/audio/faded_audio.wav")
    video_output = Path("./tmp/output")
