from pathlib import Path
from dataclasses import dataclass
from pathlib import Path

import pygame

pygame.font.init()

@dataclass
class Colors:
    background = pygame.Color("#151515")
    background_music_elements = pygame.Color(0,0,0,150)
    bar_bright = pygame.Color("#CCCCCC")
    bar_dim = pygame.Color("#747474")
    bar_dark = pygame.Color("#222222")
    wave = pygame.Color("#E7E7E7")
    text = pygame.Color("#EEEEEE")
    text_selection = pygame.Color("#BF7F0F")
    text_border = pygame.Color("#5A149C")
    checkbox_border = pygame.Color(100,100,100,100)
    checkbox_checkmark = pygame.Color("white")

@dataclass
class Paths:
    images = Path("./tmp/images")
    tmp_audio = Path("./tmp/audio/faded_audio.wav")
    video_output = Path("./tmp/output")

@dataclass
class Fonts:
    font_path = Path("./assets/AgaveNerdFontMono-Regular.ttf")
    small = pygame.Font(font_path, 12)
    medium = pygame.Font(font_path, 20)
    large = pygame.Font(font_path, 30)

@dataclass
class SVGs:
    clip = pygame.image.load_sized_svg("./assets/clipping.svg", (25,25))

@dataclass
class Sizes:
    window = pygame.Vector2(500, 900)
    background_fade = 10        # amount of pixels to fade background to alpha 0
    soundwave_height = 100      # amount of pixels
    scrubbar_height = 50        # amount of pixels
    equalizer_height = 100      # amount of pixels
    render_framerate = 60       # fps for rendered video
    fft_window_size = 12000     # amount of samples
    fft_hop_size = 1024         # amount of samples
    fft_low_freq = 30           # lowest frequency for equalizer
    fft_high_freq = 16000       # highest frequency for equalizer
    amount_bars = 70            # amount of bars for eq and scrub bar
    bar_padding = 3             # amount of pixels in x between bars
    text_selection_radius = 3   # edge radius for selection rect in TextField
    checkbox_width = 2          # width of the rect for checkbox
    checkbox_radius = 3         # radius of the rect for checkbox
    meta_tag_padding = 5        # amount of pixels in x bewteen text and checkbox
    meta_tag_margin = 4         # amount of pixels arround textfield for fading

@dataclass
class Positions:
    soundwave = pygame.Rect(0, 0, Sizes.window.x, Sizes.soundwave_height)
    equalizer = pygame.Rect(0, Sizes.window.y - Sizes.equalizer_height, Sizes.window.x, Sizes.equalizer_height)
    scrubbar = pygame.Rect(0, Sizes.window.y - Sizes.equalizer_height - Sizes.scrubbar_height, Sizes.window.x, Sizes.scrubbar_height)
    clipper = pygame.Vector2(5,5)
    clipper_checkbox = pygame.Rect(5, Sizes.window.y - Sizes.equalizer_height - Sizes.scrubbar_height - Fonts.medium.get_height()*4 - 5, 20, 20)
    current_time_textfield = pygame.Vector2(5, Sizes.window.y - Sizes.equalizer_height - Sizes.scrubbar_height - Fonts.medium.get_height()*3)
    start_fade_textfield = pygame.Vector2(5, Sizes.window.y - Sizes.equalizer_height - Sizes.scrubbar_height - Fonts.medium.get_height()*2)
    end_fade_textfield = pygame.Vector2(5, Sizes.window.y - Sizes.equalizer_height - Sizes.scrubbar_height - Fonts.medium.get_height())
