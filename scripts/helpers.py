from io import BytesIO
from pathlib import Path

import pygame
from tinytag import TinyTag
from PIL import Image, ImageFilter

from .const import Paths, Sizes

def get_metadata(file_path: Path) -> dict:
    """Extract metadata from any supported audio file.
    Returns a dictionary with keys:
        title, artist, album, genre, date, duration, sample_rate, bitrate, cover_art
    """

    tag = TinyTag.get(file_path, image=True)
    image = tag.images.any
    image_blur = None

    if image:
        image, image_blur = convert_cover(image.data)

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
        "cover_art_blur": image_blur
    }

def convert_cover(cover:Path|bytes|str):
    if isinstance(cover, bytes):
        image = Image.open(BytesIO(cover))
    elif isinstance(cover, Path):
        image = Image.open(cover)
    elif isinstance(cover, str):
        image = Image.open(cover)
    else:
        raise TypeError

    if image.mode == "RGB":
        format = "RGB"
    elif image.mode == "RGBA":
        format = "RGBA"
    else:
        image.convert("RGB")
        format = "RGB"

    image_blur = image.filter(ImageFilter.GaussianBlur(radius=Sizes.blur_radius))
    image = pygame.image.frombytes(image.tobytes(), image.size, format)
    image_blur = pygame.image.frombytes(image_blur.tobytes(), image_blur.size, format)

    return image, image_blur

def mkdirs():
    Paths.images.mkdir(parents=True, exist_ok=True)
    Paths.tmp_audio.parent.mkdir(parents=True, exist_ok=True)
    Paths.video_output.mkdir(parents=True, exist_ok=True)

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
