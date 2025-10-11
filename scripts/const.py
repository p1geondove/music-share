from pathlib import Path
from dataclasses import dataclass
from typing import TypedDict

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
    custom = lambda x:pygame.Font(Fonts.font_path, x)


@dataclass
class Sizes:
    window = 430, 900           # preview window size
    window_max_size = 900
    window_render = 1280, 2700  # render window size
    blur_radius = 10            # gaussian image blur radius
    background_fade = 0.2       # factor of element height
    soundwave_height = 0.1      # factor of winheight
    soundwave_samples = 500     # amount of samples in the window
    scrubbar_height = 0.05      # factor of winheight
    equalizer_height = 0.1      # factor of winheight
    render_framerate = 60       # fps for rendered video
    fft_window_size = 12000     # amount of samples
    fft_hop_size = 1024         # amount of samples
    fft_low_freq = 30           # lowest frequency for equalizer
    fft_high_freq = 16000       # highest frequency for equalizer
    song_fade_time = 1          # amount of seconds used for fading music
    amount_bars = 70            # amount of bars for eq and scrub bar
    bar_padding = 3             # amount of pixels in x between bars
    text_selection_radius = 3   # edge radius for selection rect in TextField
    checkbox_width = 2          # width of the rect for checkbox
    checkbox_radius = 3         # radius of the rect for checkbox
    meta_tag_padding = 5        # amount of pixels in x bewteen text and checkbox
    meta_tag_margin = 4         # amount of pixels arround textfield for fading
    clipper_svg = 25            # square size of clipper svg in pixels

@dataclass
class SVGs:
    clip = pygame.image.load_sized_svg("./assets/clipping.svg", (Sizes.clipper_svg,Sizes.clipper_svg))

@dataclass
class AllowedFileTypes:
    audio = {".mp3", ".wav", ".flac", ".opus"}
    image = {".bmp", ".gif", ".jpeg", ".jpg", ".png"}

@dataclass
class PositionsConst:
    clipper = pygame.Vector2(5,5)

class Positions(TypedDict):
    soundwave: pygame.Rect
    eqalizer: pygame.Rect
    scrubbar: pygame.Rect
    current_time_textfield: pygame.Vector2
    start_fade_textfield: pygame.Vector2
    end_fade_textfield: pygame.Vector2
    clipper_checkbox: pygame.Rect
    resolution_textfield: pygame.Vector2
