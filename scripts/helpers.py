from io import BytesIO
from pathlib import Path
import numpy as np

import pygame
import soundfile as sf
from tinytag import TinyTag
from PIL import Image, ImageFilter

from .const import Paths, Sizes, Colors, Fonts, Positions

def get_metadata(file_path: Path) -> dict:
    """Extract metadata from any supported audio file.
    Returns a dictionary with keys:
        title, artist, album, genre, date, duration, sample_rate, bitrate, cover_art
    """

    tag = TinyTag.get(file_path, image=True)
    image = tag.images.any

    if image:
        image = image.data

    duration = time_to_str(tag.duration) if tag.duration else None
    bitrate = f"{tag.bitrate:.1f} kbps" if tag.bitrate else None

    return {
        "title": tag.title,
        "artist": tag.artist,
        "album": tag.album,
        "genre": tag.genre,
        "date": tag.year,
        "duration": duration,
        "sample_rate": tag.samplerate,
        "bitrate": bitrate,
        "cover_art": image,
    }

def convert_cover(cover:Path|bytes|str|None, size:tuple[int,int]):
    if isinstance(cover, bytes):
        image = Image.open(BytesIO(cover))
    elif isinstance(cover, Path):
        image = Image.open(cover)
    elif isinstance(cover, str):
        image = Image.open(cover)
    elif cover is None:
        surface = pygame.Surface(size)
        surface.fill(Colors.background)
        txt_surface = Fonts.custom(max(size)//20).render("No cover", True, Colors.text, Colors.background)
        x = (size[0] - txt_surface.width) // 2
        y = (size[1] - txt_surface.height) // 2
        surface.blit(txt_surface, (x,y))
        return surface
    else:
        raise TypeError("cover must be raw bytes or path to file")

    if image.mode == "RGB":
        format = "RGB"
    elif image.mode == "RGBA":
        format = "RGBA"
    else:
        image = image.convert("RGB")
        format = "RGB"

    image_blur = image.filter(ImageFilter.GaussianBlur(radius=Sizes.blur_radius))
    image = pygame.image.frombytes(image.tobytes(), image.size, format) #breaks here: ValueError: Bytes length does not equal format and resolution size
    image_blur = pygame.image.frombytes(image_blur.tobytes(), image_blur.size, format)

    cover_surface = pygame.Surface(size, pygame.SRCALPHA)
    image = resize_surface(image, size, True)
    image_blur = resize_surface(image_blur, size, False)
    cover_surface.blit(image_blur)
    cover_surface.blit(image)

    return cover_surface

def resize_surface(surface:pygame.Surface, size:tuple[int,int], fit:bool):
    """ scales surface, fit:True means it fits in the size result in blackbars(alpha), False means potential cutting"""
    new_surface = pygame.Surface(size, pygame.SRCALPHA) # create new destination surface
    factor_width = size[0] / surface.width # size difference in x, <1:scale down, >1:scale up
    factor_height = size[1] / surface.height # size difference in y
    factor = min(factor_width, factor_height) if fit else max(factor_width, factor_height) # scale factor depending of fit option
    new_width = int(surface.width * factor + .5) # dynamically get new image size
    new_height = int(surface.height * factor + .5)
    surface = pygame.transform.scale(surface, (new_width, new_height)) # scale image to size
    offset_x = (size[0] - surface.width) / 2 # offset from image to surface topleft
    offset_y = (size[1] - surface.height) / 2
    new_surface.blit(surface, (offset_x, offset_y))
    return new_surface

def fade_song(song_data:np.ndarray, sample_rate:int, start:float, end:float):
    fade_samples = Sizes.song_fade_time * sample_rate
    fade_in_start = int(start * sample_rate)
    fade_out_start = int(end * sample_rate - fade_samples)
    faded_song = song_data.copy()
    amount_channels = 1
    if len(song_data.shape) > 1:
        amount_channels = song_data.shape[1]

    if amount_channels > 1:
        fade_in = np.linspace(0,1,fade_samples)[:, np.newaxis]
        fade_out = np.linspace(1,0,fade_samples)[:, np.newaxis]
        faded_song[:fade_in_start, :] = 0
        faded_song[fade_out_start+fade_samples:, :] = 0
        faded_song[fade_in_start:fade_in_start+fade_samples, :] *= fade_in
        faded_song[fade_out_start:fade_out_start+fade_samples, :] *= fade_out
    else:
        fade_in = np.linspace(0,1,fade_samples)
        fade_out = np.linspace(1,0,fade_samples)
        faded_song[:fade_in_start] = 0
        faded_song[fade_out_start+fade_samples:] = 0
        faded_song[fade_in_start:fade_in_start+fade_samples] *= fade_in
        faded_song[fade_out_start:fade_out_start+fade_samples] *= fade_out

    sf.write(Paths.tmp_audio, faded_song, sample_rate)

def get_element_positions(winsize: tuple[int, int]) -> Positions:
    soundwave = pygame.Rect(0, 0, winsize[0], Sizes.soundwave_height * winsize[1])
    equalizer = pygame.Rect(0, winsize[1] - Sizes.equalizer_height * winsize[1], winsize[0], Sizes.equalizer_height * winsize[1])
    scrubbar = pygame.Rect(0, equalizer.top - Sizes.scrubbar_height * winsize[1], winsize[0], Sizes.scrubbar_height * winsize[1])
    end_fade_textfield = pygame.Vector2(5, scrubbar.top - Fonts.medium.get_height())
    start_fade_textfield = pygame.Vector2(5, end_fade_textfield.y - Fonts.medium.get_height())
    current_time_textfield = pygame.Vector2(5, start_fade_textfield.y - Fonts.medium.get_height())
    clipper_checkbox = pygame.Rect(5, current_time_textfield.y - Fonts.medium.get_height(), Fonts.medium.get_height(), Fonts.medium.get_height())
    resolution_textfield = pygame.Vector2(winsize[0] - Fonts.medium.size(" "*9)[0], scrubbar.top - Fonts.medium.get_height())

    return {
        "soundwave": soundwave,
        "eqalizer": equalizer,
        "scrubbar": scrubbar,
        "current_time_textfield": current_time_textfield,
        "start_fade_textfield": start_fade_textfield,
        "end_fade_textfield": end_fade_textfield,
        "clipper_checkbox": clipper_checkbox,
        "resolution_textfield": resolution_textfield
    }

def tmp_cleanup():
    Paths.images.mkdir(parents=True, exist_ok=True)
    Paths.tmp_audio.parent.mkdir(parents=True, exist_ok=True)
    Paths.video_output.mkdir(parents=True, exist_ok=True)
    Paths.tmp_audio.unlink(True)
    for f in Paths.images.iterdir():
        f.unlink()

def time_to_str(seconds:float) -> str:
    """ formats a float in seconds to minutes and seconds string """
    min = int(seconds / 60)
    sec = int(seconds % 60)
    ms = int(seconds % 1 * 1000)
    return f"{min}:{sec:02d}.{ms:03d}"

def str_to_time(string:str) -> float|None:
    """ basically inverse of time_to_str """
    try:
        min, rest = string.split(":")
        sec, ms = rest.split(".")
        return int(min)*60 + int(sec) + float(ms)/1000
    except:
        return
