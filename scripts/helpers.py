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
            format = "RGB"

        image = pygame.image.frombytes(pil_image.tobytes(), pil_image.size, format)
        image_blur = pygame.image.frombytes(pil_image_blur.tobytes(), pil_image_blur.size, format)


    return {
        "title": tag.title,
        "artist": tag.artist,
        "album": tag.album,
        "genre": tag.genre,
        "date": tag.year,
        "duration": tag.duration,
        "sample_rate": tag.samplerate,
        "bitrate": tag.bitrate,
        "cover_art": image,
        "cover_art_blur": image_blur
    }

def mkdirs():
    Paths.images.mkdir(parents=True, exist_ok=True)
    Paths.tmp_audio.parent.mkdir(parents=True, exist_ok=True)
    Paths.video_output.mkdir(parents=True, exist_ok=True)
