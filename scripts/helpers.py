from io import BytesIO
from pathlib import Path

import pygame
from tinytag import TinyTag
from PIL import Image, ImageFilter

# from .ntimer import timer
from .const import Paths

# @timer
def get_metadata(file_path: Path) -> dict:
    """Extract metadata from any supported audio file.
    Returns a dictionary with keys:
        title, artist, album, genre, date, duration, sample_rate, bitrate, cover_art
    """

    tag = TinyTag.get(file_path, image=True)
    image = tag.images.any
    image_blur = None

    if image:
        pil_image = Image.open(BytesIO(image.data))
        pil_image_blur = pil_image.filter(ImageFilter.GaussianBlur(radius=10))

        if pil_image.mode == "RGB":
            format = "RGB"
        elif pil_image.mode == "RGBA":
            format = "RGBA"
        else:
            pil_image = pil_image.convert("RGB")
            pil_image_blur = pil_image_blur.convert("RGB")
            format = "RGB"

        image = pygame.image.frombytes(pil_image.tobytes(), pil_image.size, format)
        image_blur = pygame.image.frombytes(pil_image_blur.tobytes(), pil_image_blur.size, format)

    duration = time_to_str(tag.duration) if tag.duration else None
    bitrate = f"{tag.bitrate:.0f} kbps"

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
