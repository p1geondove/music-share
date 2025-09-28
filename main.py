import sys
import time
import subprocess
from io import BytesIO
from pathlib import Path

import pygame
import librosa
from PIL import Image, ImageFilter
from tinytag import TinyTag
import soundfile as sf
import numpy as np


from ntimer import fmt_ns, timer

BACKGROUND_COLOR = pygame.Color("grey15")

class MusicPlayer:
    def __init__(self, song_path:Path, autoplay=True, startpos=0.):
        start_ns = time.perf_counter_ns()
        self.beginnig = 0
        self.current_time = 0
        self.beginnig = time.time()


        pygame.mixer_music.load(song_path)
        pygame.mixer_music.play()

        if startpos>0.:
            self.play_from_position(startpos)

        if autoplay == False:
            pygame.mixer_music.pause()

        print(f"music player took {fmt_ns(time.perf_counter_ns() - start_ns)}") # 180 us

    def play_from_position(self, position_seconds):
        self.current_time = position_seconds
        self.beginnig = time.time() - position_seconds
        if not pygame.mixer_music.get_busy():
            pygame.mixer_music.play()
            pygame.mixer_music.pause()
        pygame.mixer.music.set_pos(position_seconds)

    def get_current_position(self):
        if pygame.mixer_music.get_busy():
            return time.time() - self.beginnig
        return self.current_time

    def pause(self):
        self.current_time = self.get_current_position()
        pygame.mixer_music.pause()

    def resume(self):
        self.beginnig = time.time() - self.current_time
        pygame.mixer_music.unpause()

    def set_song(self, song_path:Path):
        pygame.mixer_music.load(song_path)
        self.beginnig = time.time()
        pygame.mixer_music.play()

class ScrubBar:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int) -> None:
        start = time.perf_counter_ns()
        self.rect = rect
        self.song_data = song_data
        self.sample_rate = sample_rate
        self.song_length = len(song_data) / sample_rate

        self.current_time = 0.0
        self.start_pos = 0.0
        self.end_pos = self.song_length
        self.fade_time = 1
        self.fade_samples = int(self.fade_time * self.sample_rate)
        self.faded_audio_tmp_path = Path("./tmp/audio/faded_audio.wav")
        self.pressed_left = False
        self.pressed_right = False

        block_size = int(len(song_data) / self.rect.width) # calculate how many samples one pixel is
        blocks = [song_data[start:start+block_size] for start in range(0,len(song_data),block_size)] # split whole song into blocks
        self.levels = np.array([np.sqrt(np.mean(block**2)) for block in blocks]) # caluclate levels
        self.levels = self.levels / max(self.levels) * self.rect.height # normalize and fit to surface height

        print(f"scrub bar took {fmt_ns(time.perf_counter_ns() - start)}") # 4 ms

    def draw(self) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        for x_pos, level in enumerate(self.levels):
            time_s = x_pos / self.rect.width * self.song_length
            color = "grey"
            if time_s < self.current_time:
                color = "orange"
            if time_s < self.start_pos or time_s > self.end_pos:
                color = "grey20"
            pygame.draw.line(surface, color, (x_pos, self.rect.height), (x_pos, self.rect.height-level))

        return surface, self.rect.topleft

    def fade(self):
        # fade_samples = fade_time * self.sample_rate
        fade_in = np.linspace(0,1,self.fade_samples)
        fade_out = np.linspace(1,0,self.fade_samples)
        fade_in_start = int(self.start_pos * self.sample_rate)
        fade_out_start = int(self.end_pos * self.sample_rate - self.fade_samples)
        faded_song = self.song_data.copy()
        faded_song[:fade_in_start] = 0
        faded_song[fade_out_start+self.fade_samples:] = 0
        faded_song[fade_in_start:fade_in_start+self.fade_samples] *= fade_in
        faded_song[fade_out_start:fade_out_start+self.fade_samples] *= fade_out
        sf.write(self.faded_audio_tmp_path, faded_song, self.sample_rate)
        return self.sample_rate, self.faded_audio_tmp_path, faded_song

    def handle_event(self, event:pygame.Event):
        special_events = []

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 1: # left mouse button pressed
                    self.pressed_left = True
                    x_loacle = int(event.pos[0]) - self.rect.left
                    self.current_time = min(max(0,x_loacle / self.rect.width * self.song_length), self.song_length)
                    special_events.append("playing_pos changed")

                elif event.button == 3: # righ mouse button pressed
                    self.pressed_right = True
                    x_loacle = int(event.pos[0]) - self.rect.left
                    song_pos = min(max(0,x_loacle / self.rect.width * self.song_length), self.song_length)
                    deltas = (abs(self.start_pos - song_pos), abs(self.end_pos - song_pos))

                    if deltas[0] < deltas[1]:
                        self.start_pos = song_pos
                        special_events.append("start_pos changed")
                    else:
                        self.end_pos = song_pos
                        special_events.append("end_pos changed")

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # left mouse button released
                self.pressed_left = False
            elif event.button == 3: # right mouse button released
                self.pressed_right = False
                x_loacle = int(event.pos[0]) - self.rect.left
                song_pos = min(max(0,x_loacle / self.rect.width * self.song_length), self.song_length)
                deltas = (abs(self.start_pos - song_pos), abs(self.end_pos - song_pos))
                if deltas[0] < deltas[1]:
                    self.start_pos = song_pos
                    special_events.append("start_pos changed")
                else:
                    self.end_pos = song_pos
                    special_events.append("end_pos changed")
                

        if event.type == pygame.MOUSEMOTION:
            if self.pressed_left: # scrub along the time axis
                x_loacle = int(event.pos[0]) - self.rect.left
                self.current_time = min(max(0,x_loacle / self.rect.width * self.song_length), self.song_length)
                special_events.append("playing_pos changed")

            elif self.pressed_right: # scrub the start or end positions
                x_loacle = int(event.pos[0]) - self.rect.left
                song_pos = min(max(0,x_loacle / self.rect.width * self.song_length), self.song_length)
                deltas = (abs(self.start_pos - song_pos), abs(self.end_pos - song_pos))

                if deltas[0] < deltas[1]:
                    self.start_pos = song_pos
                    special_events.append("start_pos changed")
                else:
                    self.end_pos = song_pos
                    special_events.append("end_pos changed")

        return special_events

class SoundWave:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int, amount_samples:int = 500) -> None:
        self.rect = rect
        self.song_data = song_data * rect.height / 2 + rect.height / 2
        self.sample_rate = sample_rate
        self.amount_samples = amount_samples
        self.song_length = len(song_data) / sample_rate

    def draw(self, position:float) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        start_pos = min(int(position * self.sample_rate), self.song_data.size - self.amount_samples - 1)
        samples = self.song_data[start_pos : start_pos + self.amount_samples]
        x_pos = np.arange(samples.size)
        points = np.stack((x_pos, samples), axis=1)
        pygame.draw.lines(surface, "grey", False, points)
        return surface, self.rect.topleft

class Equalizer:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int, window_size:int = 8192, hop_size:int = 1024):
        start_ns = time.perf_counter_ns()
        # put arguments in valiables
        self.rect = rect
        self.sample_rate = sample_rate
        self.hop_size = hop_size

        # fft constants
        amt_bands = 30
        freq_bands = np.geomspace(20,20000,amt_bands)
        self.amount_windows = (len(song_data) - window_size) // hop_size + 1
        bin_freqs = np.fft.rfftfreq(window_size, 1/sample_rate)
        target_bins = [np.argmin(np.abs(bin_freqs - f)) for f in freq_bands]
        self.eq_data = np.zeros((self.amount_windows, len(freq_bands)))
        
        # calculate fft
        for i in range(self.amount_windows):
            start = i * hop_size
            end = start + window_size
            window = song_data[start:end] * np.hanning(window_size)
            fft = np.fft.rfft(window)
            self.eq_data[i,:] = np.abs(fft[target_bins])

        # normalize fft
        self.eq_data = np.log10(self.eq_data+1e-10) # log that bish
        self.eq_data = np.clip(self.eq_data / np.max(self.eq_data) * 11, 0, 10) # normalize and scale to surface
        self.eq_data = self.eq_data.astype(int)
        print(f"equalizer took {fmt_ns(time.perf_counter_ns() - start_ns)}") # 130 ms

        # drawing constants
        self.padding_x = 2
        self.padding_y = 1
        self.bar_width = rect.width / len(freq_bands) - self.padding_x
        block_height = rect.height/10 - self.padding_y
        self.x_positions = [self.bar_width * x + x*self.padding_x for x in range(len(freq_bands))]
        self.bars = {
            0: pygame.Surface((self.bar_width,rect.height), pygame.SRCALPHA)
        }

        bar_surf = pygame.Surface((self.bar_width,rect.height), pygame.SRCALPHA)
        for x in range(10): # levels from 0 to 10
            if x < 5:
                color = "#239617"
            elif x < 8:
                color = "#d4c522"
            else:
                color = "#b80d0d"
            pos = 0, x*block_height+x*self.padding_y, self.bar_width, block_height
            # print(pos)
            pygame.draw.rect(bar_surf,color,pos)
            self.bars[x+1] = bar_surf.copy()
        # print(self.eq_data, np.min(self.eq_data), np.max(self.eq_data))
        # print(self.bars)

    def draw(self, position:float) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        frame_index = min(int(position * self.sample_rate / self.hop_size), self.amount_windows-1)
        eq_data = self.eq_data[frame_index]

        # for i, val in enumerate(eq_data):
        for x, val in zip(self.x_positions, eq_data):
            # surface.blit(self.bars[val], (i*self.bar_width+i*self.padding_x,0))
            surface.blit(self.bars[val], (x,0))
            # print(val)
            # bar_rect = (
            #     i * self.bar_width,
            #     self.rect.height - val,
            #     self.bar_width,
            #     val
            # )

            # pygame.draw.rect(
            #     surface,
            #     "orange",
            #     bar_rect
            # )

        return surface, self.rect.topleft

class Orchestrator:
    def __init__(self, window:pygame.Surface, song_path:Path|None = None) -> None:
        start = time.perf_counter_ns()
        self.window = window
        self.surface_cover = window.copy()
        self.surface_info = window.copy()
        self.initialized = False
        self.images_dir = Path("./tmp/images")
        self.render_framerate = 60

        # check if a file path has been given
        if not song_path:
            self.draw_info("No song loaded")
            return

        # check if the file is supported audio file
        self.song_path = song_path
        if song_path.suffix in (".jpg", ".jpeg", ".bmp", ".png", ".gif"):
            self.draw_info("Load audio first")
            return

        if song_path.suffix not in (".mp3", ".flac", ".opus", ".wav"):
            self.draw_info(f"{song_path.suffix} not supported")
            return

        # get metadata of the song
        self.metadata = get_metadata(song_path)
        self.convert_cover()
        self.playing = False
        song_data, sample_rate = sf.read(song_path)
        self.song_data = song_data
        self.sample_rate = sample_rate

        # convert audio data to mono and normalize
        self.draw_info("Converting")
        start_norm = time.perf_counter_ns()
        if len(self.song_data.shape) > 1:
            self.song_data = np.mean(self.song_data, axis=1)
        song_mono_norm = self.song_data / max(abs(max(self.song_data)), abs(min(self.song_data)))
        print(f"converting audio took {fmt_ns(time.perf_counter_ns() - start_norm)}") # 400 ms

        # create a music player
        self.music_player = MusicPlayer(song_path, self.playing)

        # create sound wave top
        self.draw_info("Setting up sound_wave")
        self.sound_wave = SoundWave(
            pygame.Rect(0,0,window.width,100),
            song_mono_norm,
            self.sample_rate
        )

        # create a scrub bar bottom left
        self.draw_info("Setting up scrub bar")
        self.scrub_bar = ScrubBar(
            pygame.Rect(0, window.height-150, window.width, 50),
            song_mono_norm,
            self.sample_rate
        )

        # create equalizer bottom right
        self.draw_info("Setting up equalizer")
        self.equalizer = Equalizer(
            pygame.Rect(0, window.height-100, window.width, 100),
            song_mono_norm,
            self.sample_rate
        )

        # say that its fully initialized
        self.initialized = True
        print(f"orchester took {fmt_ns(time.perf_counter_ns() - start)}") # 700 ms

    @timer # 400 us
    def convert_cover(self):
        """ loads the cover art from metadata and adjusts size, or prints text that no cover has been found """
        self.surface_cover.fill(BACKGROUND_COLOR)

        if not self.metadata["cover_art"]:
            txt_surface = pygame.Font.render(pygame.font.SysFont(None,50), "No cover", True, "grey")
            x = self.surface_cover.width/2 - txt_surface.width/2
            y = self.surface_cover.height/2 - txt_surface.height/2
            self.surface_cover.blit(txt_surface, (x,y))
            return

        cover = self.metadata["cover_art"]
        cover_blur = self.metadata["cover_art_blur"]

        factor_width = self.window.width / cover_blur.width
        factor_height = self.window.height / cover_blur.height

        factor = max(factor_width, factor_height)
        new_width = cover_blur.width * factor
        new_height = cover_blur.height * factor
        cover_blur = pygame.transform.scale(cover_blur, (new_width, new_height))
        offset_x = (self.window.width - cover_blur.width) / 2
        offset_y = (self.window.height - cover_blur.height) / 2
        self.surface_cover.blit(cover_blur, (offset_x, offset_y))


        factor = min(factor_width, factor_height)
        new_width = cover.width * factor
        new_height = cover.height * factor
        cover = pygame.transform.scale(cover, (new_width, new_height))
        offset_x = (self.window.width - cover.width) / 2
        offset_y = (self.window.height - cover.height) / 2
        self.surface_cover.blit(cover, (offset_x, offset_y))

    @timer # 10 ms
    def draw_info(self, txt:str):
        """ prints text in the middle of the screen """
        self.surface_info.fill(BACKGROUND_COLOR)
        txt_surface = pygame.Font.render(pygame.font.SysFont(None,50), txt, True, "grey")
        x = self.surface_info.width/2 - txt_surface.width/2
        y = self.surface_info.height/2 - txt_surface.height/2
        self.surface_info.blit(txt_surface, (x,y))
        self.window.blit(self.surface_info, (0,0))
        pygame.display.flip()

    def handle_event(self, event:pygame.Event):
        # handle events, initialized or not
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

            elif event.key == pygame.K_r:
                self.render()

        elif event.type == pygame.DROPFILE:
            path = Path(event.file)
            if self.initialized and path.suffix in (".jpg", ".jpeg", ".bmp", ".png", ".gif"):
                self.metadata["cover_art"] = pygame.image.load(path)
                self.convert_cover()
            else:
                return Orchestrator(self.window, Path(event.file))

        # handle only these events when initialized
        if not self.initialized:
            return

        special_events = []
        special_events.extend(self.scrub_bar.handle_event(event))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.playing = not self.playing
                if self.playing:
                    self.music_player.resume()
                else:
                    self.music_player.pause()


        for special_event in special_events:
            if special_event == "playing_pos changed":
                self.music_player.play_from_position(self.scrub_bar.current_time)
                scrub_surface, pos = self.scrub_bar.draw()
                self.window.blit(scrub_surface, pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3 and (special_event == "start_pos changed" or special_event == "end_pos changed"):
                    sample_rate, faded_song_path, faded_song_data = self.scrub_bar.fade()
                    self.music_player = MusicPlayer(faded_song_path, startpos=self.scrub_bar.current_time)
                    # self.sound_wave = SoundWave(self.sound_wave.rect, faded_song_data, sample_rate)
                    # self.equalizer = Equalizer(self.equalizer.rect, faded_song_data, sample_rate)
                    # self.scrub_bar = ScrubBar(self.scrub_bar.rect, faded_song_data, sample_rate)

    def draw(self):
        self.window.fill(BACKGROUND_COLOR)

        if not self.initialized:
            self.window.blit(self.surface_info)
            return


        time_pos = self.music_player.get_current_position()
        self.scrub_bar.current_time = time_pos
        self.window.blits([
            (self.surface_cover, (0,0)),
            self.scrub_bar.draw(),
            self.sound_wave.draw(time_pos),
            self.equalizer.draw(time_pos)
        ])

    def render(self):
        # surface = self.window.copy()
        surface = pygame.Surface(self.window.size, pygame.SRCALPHA)
        fade_surface = surface.copy()
        time_pos = self.scrub_bar.start_pos
        frame_num = 0
        start = self.scrub_bar.start_pos
        end = self.scrub_bar.end_pos
        dur = end - start
        fade_dur = self.scrub_bar.fade_time
        total_frames = int(dur * self.render_framerate)

        # deleting old images
        for f in self.images_dir.iterdir():
            f.unlink()

        print("staring render...")

        while time_pos < self.scrub_bar.end_pos:
            print(f"{frame_num}/{total_frames}", end="\r")
            self.scrub_bar.current_time = time_pos
            surface.blits([
                (self.surface_cover, (0,0)),
                self.scrub_bar.draw(),
                self.sound_wave.draw(time_pos),
                self.equalizer.draw(time_pos)
            ])

            if time_pos < start + fade_dur:
                alpha = 255 - int((time_pos-start) / fade_dur * 255)
                fade_surface.fill((0,0,0,alpha))
                surface.blit(fade_surface, (0,0))

            elif time_pos > end - fade_dur:
                alpha = 255 - int((end-time_pos) / fade_dur * 255)
                fade_surface.fill((0,0,0,alpha))
                surface.blit(fade_surface, (0,0))

            file_path = self.images_dir / f"{frame_num:05d}.bmp"
            pygame.image.save(surface, file_path)
            time_pos += 1/self.render_framerate
            frame_num += 1
        
        print(f"\nstitching together")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(self.render_framerate),
            "-start_number", "0",
            "-i", str(self.images_dir)+r"/%05d.bmp",
            "-ss", str(start),
            "-t", str(dur),
            "-i", str(self.song_path),
            "-af", f"afade=t=in:st=0:d={fade_dur},afade=t=out:st={dur-fade_dur}:d={fade_dur}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-r", str(self.render_framerate),
            "tmp/output.mp4"
        ]

        print(f"ffmpeg command:\n{' '.join(cmd)}")

        subprocess.run(cmd)

        print(f"done rendering! video is at ./tmp/output.mp4")

@timer
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

def main():
    pygame.mixer.init()
    pygame.font.init()

    width = 500
    height = 900
    window = pygame.display.set_mode((width, height))
    clock = pygame.Clock()
    orchester = Orchestrator(window, None)

    while True:
        for event in pygame.event.get():
            if o:=orchester.handle_event(event):
                orchester = o

        orchester.draw()
        pygame.display.flip()
        pygame.display.set_caption(f"{clock.get_fps():.0f}")
        clock.tick()

if __name__ == "__main__":
    main()
