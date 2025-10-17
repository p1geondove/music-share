import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import TypedDict

import pygame

pygame.font.init()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


@dataclass
class Colors:
    background = pygame.Color("#151515")                # default background color
    background_music_elements = pygame.Color(0,0,0,150) # trasnparent background for music elements
    bar_bright = pygame.Color("#CCCCCC")                # bar color of equalizer and scrubbar left from current time pos
    bar_dim = pygame.Color("#747474")                   # bar color of scrubbar right from currentpos (unplayed)
    bar_dark = pygame.Color("#222222")                  # lower part of scrubbar for start / end position of render section
    wave = pygame.Color("#E7E7E7")                      # color for soundwave
    text = pygame.Color("#EEEEEE")                      # all text has the same color
    text_selection = pygame.Color("#BF7F0F")            # selection of textfield as "background color"
    text_background = pygame.Color("#5A149C")           # background for textfield, only used for current, start and end pos controls
    checkbox_border = pygame.Color(100,100,100,100)     # border color for checkbox
    checkbox_checkmark = pygame.Color("white")          # color of the checkmark


@dataclass
class Paths:
    images = Path(resource_path("tmp/images"))                      # temporary images to be stiched together by ffmpeg
    tmp_audio = Path(resource_path("tmp/audio/faded_audio.wav"))    # temporary audio file that has start and end faded
    video_output = Path(resource_path("tmp/output"))                # output folder of the rendered videos


@dataclass
class Fonts:
    font_path = Path(resource_path("assets/AgaveNerdFontMono-Regular.ttf")) # font path...
    medium = pygame.Font(font_path, 20)                                     # used for time control emelents
    custom = lambda x:pygame.Font(Fonts.font_path, x)                       # used for metadata tags and infos in the middle of the screen


@dataclass
class Sizes:
    window = 405, 900           # preview window size
    preview_fps = 60            # limit to 60 fps
    window_max_size = 900       # set preview window to constant size depending on render size
    window_max_ratio = 0.35     # max screen ratio
    window_render = 1080, 2400  # render window size
    blur_radius = 10            # gaussian image blur radius
    background_fade = 0.2       # factor of element height
    soundwave_height = 0.1      # factor of winheight
    soundwave_samples = 500     # amount of samples in the window
    scrubbar_height = 0.05      # factor of winheight
    equalizer_height = 0.1      # factor of winheight
    render_framerate = 60       # fps for rendered video
    fft_window_size = 10000     # amount of samples
    fft_hop_size = 1024         # amount of samples
    fft_low_freq = 50           # lowest frequency for equalizer
    fft_high_freq = 16000       # highest frequency for equalizer
    song_fade_time = 1          # amount of seconds used for fading music
    amount_bars = 100           # amount of bars for eq and scrub bar
    bar_padding = 0.15          # ratio of barwidth / gap
    text_selection_radius = 3   # edge radius for selection rect in TextField
    checkbox_width = 2          # width of the rect for checkbox
    checkbox_radius = 3         # radius of the rect for checkbox
    meta_tag_padding = 5        # amount of pixels in x bewteen text and checkbox
    meta_tag_margin = 4         # amount of pixels arround textfield for fading
    clipper_svg = 0.2           # ratio of svg size (square) / soundwave_surface height


@dataclass
class SVGs:
    clip = lambda x:pygame.image.load_sized_svg(resource_path("assets/clipping.svg"), (x,x)) # made this a seperate class in case i add more images/svgs


@dataclass
class AllowedFileTypes:
    audio = {".mp3", ".wav", ".flac", ".opus"}          # only these really work with pygame.mixer_music without too much hassle
    image = {".bmp", ".gif", ".jpeg", ".jpg", ".png"}   # used to load cover art seperately


class Positions(TypedDict):
    soundwave: pygame.Rect                  # soundwave.__init__ wants a rect
    eqalizer: pygame.Rect                   # equalizer.__init__ wants a rect
    scrubbar: pygame.Rect                   # scrubbar.__init__ wants a Rect
    current_time_textfield: pygame.Vector2  # any textfield takes tuple[int,int] or Vector2
    start_fade_textfield: pygame.Vector2
    end_fade_textfield: pygame.Vector2
    resolution_textfield: pygame.Vector2
    clipper_checkbox: pygame.Rect           # checkboxes take a rect

