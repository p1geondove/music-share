import sys
import time
import subprocess
from pathlib import Path

import pygame
import numpy as np
import soundfile as sf

from .const import Colors, Paths
from .helpers import get_metadata

class MusicPlayer:
    def __init__(self, song_path:Path, autoplay=True, startpos=0.):
        self.beginnig = 0
        self.current_time = 0
        self.beginnig = time.time()
        self.playing = autoplay

        pygame.mixer_music.load(song_path)
        pygame.mixer_music.play()

        if startpos>0.:
            self.play_from_position(startpos)

        if autoplay == False:
            pygame.mixer_music.pause()

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
        self.playing = False
        self.current_time = self.get_current_position()
        pygame.mixer_music.pause()

    def resume(self):
        self.playing = True
        self.beginnig = time.time() - self.current_time
        pygame.mixer_music.unpause()

    def set_song(self, song_path:Path):
        pygame.mixer_music.load(song_path)
        self.beginnig = time.time()
        self.playing = True
        pygame.mixer_music.play()

class ScrubBar:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int, padding:int = 3, amount_bars:int = 70) -> None:
        self.rect = rect
        self.song_data = song_data
        self.sample_rate = sample_rate
        self.song_length = len(song_data) / sample_rate

        self.current_time = 0.0
        self.start_pos = 0.0
        self.end_pos = self.song_length
        self.pressed_left = False
        self.pressed_right = False

        self.calc_amplitudes(amount_bars, padding)

    def calc_amplitudes(self, amount_bars:int, padding:int):
        self.padding = padding
        self.padding_time = len(self.song_data) / self.rect.width / self.sample_rate * padding
        samples_per_bar = int(len(self.song_data) / amount_bars)
        self.bar_duration = samples_per_bar / self.sample_rate
        self.bar_width = self.rect.width / amount_bars - padding
        self.bar_radius = self.bar_width/2
        self.x_positions = np.linspace(padding/2, self.rect.width - self.bar_width - padding, amount_bars, dtype=int)
        indecies = np.linspace(0, len(self.song_data), amount_bars, dtype=int)
        blocks = [self.song_data[s:e] for s,e in zip(indecies[:-1], indecies[1:])]
        amp = np.array([np.mean(np.abs(b)) for b in blocks])
        amp /= np.max(amp)
        self.amplitude = (1 + self.rect.height - self.rect.height * amp).astype(int)

    def draw(self) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        for x_pos, amp in zip(self.x_positions, self.amplitude):
            bar_time_start = x_pos / self.rect.width * self.song_length
            bar_time_end = bar_time_start + self.bar_duration
            height = self.rect.height - amp

            # full bar
            lerp_val = min(max(0,(self.current_time - bar_time_start) / self.bar_duration),1)
            color_bar = pygame.Color.lerp(Colors.bar_dim, Colors.bar_bright, lerp_val)
            pygame.draw.rect(surface, color_bar, (x_pos, amp, self.bar_width, height))
            pygame.draw.circle(surface, color_bar, (x_pos + self.bar_radius, amp), self.bar_radius)

            # bars that signal the fade in (startpos) and fade out (endpos)
            if not (self.start_pos < bar_time_start and bar_time_end < self.end_pos): # if bar is in fade region draw the lower half differently
                if bar_time_start < self.start_pos < bar_time_end:
                    # here somehow it fills the right next bar with black, even tho im probably not touching it
                    # the fade is in the right direction, its not 1-lerp, the lerp is right
                    # just that it colors the 
                    lerp_val = min(max(0, (bar_time_end - self.start_pos) / self.bar_duration), 1)
                    print("betw", bar_time_start, self.start_pos, bar_time_end, lerp_val)
                    color_fade = pygame.Color.lerp(Colors.bar_dark, color_bar, lerp_val)

                elif bar_time_start < self.end_pos < bar_time_end:
                    # this works perfectly tho
                    lerp_val = min(max(0, (self.end_pos - bar_time_start) / self.bar_duration), 1)
                    color_fade = pygame.Color.lerp(Colors.bar_dark, color_bar, lerp_val)

                else:
                    print("else")
                    # i think its prematurely triggering this
                    # but one pixel later its properly lerping
                    color_fade = Colors.bar_dark

                # it shoudld fade from dark to color_bar the more i go to the right
                # but when i touch one pixel before the bar, color is complete bar_dark, even tho it shouldnt be touched
                # how come the fade out / end_pos works perfectly, but not the fade in? feels like i need to extedn the range of the fade in

                pygame.draw.rect(surface, color_fade, (x_pos, (self.rect.height+amp)/2, self.bar_width, height/2))
            
        return surface, self.rect.topleft

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
        x_pos = np.arange(samples.size) * surface.width / self.amount_samples
        points = np.stack((x_pos, samples), axis=1)
        pygame.draw.lines(surface, Colors.wave, False, points)
        return surface, self.rect.topleft

class Equalizer:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int, padding:int = 3, amt_bands:int = 70, window_size:int = 12000, hop_size:int = 1024):
        # put arguments in valiables
        self.rect = rect
        self.sample_rate = sample_rate
        self.hop_size = hop_size

        # fft constants
        self.amt_bands = amt_bands
        freq_bands = np.geomspace(30,16000, self.amt_bands)
        self.amount_windows = (len(song_data) - window_size) // hop_size + 1
        bin_freqs = np.fft.rfftfreq(window_size, 1/sample_rate)
        target_bins = [np.argmin(np.abs(bin_freqs - f)) for f in freq_bands]
        self.eq_data = np.zeros((self.amount_windows, len(freq_bands)))
        
        # calculate fft
        for i in range(self.amount_windows):
            start = i * hop_size
            end = start + window_size
            window = song_data[start:end] * np.blackman(window_size)
            fft = np.fft.rfft(window)
            self.eq_data[i,:] = np.abs(fft[target_bins])

        # normalize fft
        self.eq_data = np.log10(self.eq_data+1e-10) # log that bish
        self.eq_data = np.clip(self.eq_data / np.max(self.eq_data),0,1) * rect.height # normalize and scale to surface

        # drawing constants
        self.padding_x = padding
        self.bar_width = rect.width / len(freq_bands) - self.padding_x
        self.bar_radius = self.bar_width / 2
        self.x_positions = np.linspace(self.padding_x/2, rect.width-self.bar_width-self.padding_x, self.amt_bands, dtype=int)

    def draw(self, position:float) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        frame_index = min(int(position * self.sample_rate / self.hop_size), self.amount_windows-1)
        eq_data = self.eq_data[frame_index]

        # for i, val in enumerate(eq_data):
        for x, val in zip(self.x_positions, eq_data):
            pygame.draw.circle(surface, Colors.bar_bright, (x+self.bar_radius,val), self.bar_radius)
            pygame.draw.rect(surface, Colors.bar_bright, (x,0,self.bar_width,val))

        return surface, self.rect.topleft

class Orchestrator:
    def __init__(self, window:pygame.Surface, song_path:Path|None = None) -> None:
        self.window = window
        self.surface_cover = window.copy()
        self.surface_info = window.copy()
        self.initialized = False
        self.render_framerate = 60
        self.amt_bands = 70
        self.bar_padding_x = 3
        self.fade_time = 1        

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
        self.song_data, self.sample_rate = sf.read(song_path)
        self.num_channels = 1
        if len(self.song_data.shape) > 1:
            self.num_channels = self.song_data.shape[1]
        self.fade_samples = int(self.fade_time * self.sample_rate)

        # convert audio data to mono and normalize
        self.draw_info("Converting")
        if len(self.song_data.shape) > 1:
            self.song_mono = np.mean(self.song_data, axis=1)
        self.song_mono = self.song_mono / max(abs(max(self.song_mono)), abs(min(self.song_mono)))

        # create a music player
        self.music_player = MusicPlayer(song_path, self.playing)

        # create sound wave top
        self.draw_info("Setting up sound_wave")
        self.sound_wave = SoundWave(
            pygame.Rect(0,0,window.width,100),
            self.song_mono,
            self.sample_rate
        )

        # create a scrub bar bottom left
        self.draw_info("Setting up scrub bar")
        self.scrub_bar = ScrubBar(
            pygame.Rect(0, window.height-150, window.width, 50),
            self.song_mono,
            self.sample_rate,
            self.bar_padding_x,
            self.amt_bands
        )

        # create equalizer bottom right
        self.draw_info("Setting up equalizer")
        self.equalizer = Equalizer(
            pygame.Rect(0, window.height-100, window.width, 100),
            self.song_mono,
            self.sample_rate,
            self.bar_padding_x,
            self.amt_bands
        )

        # say that its fully initialized
        self.initialized = True

    def convert_cover(self):
        """ loads the cover art from metadata and adjusts size, or prints text that no cover has been found """
        # self.surface_cover.fill(BACKGROUND_COLOR)

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

    def draw_info(self, txt:str):
        """ prints text in the middle of the screen """
        self.surface_info.fill(Colors.background)
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
                    self.fade()
                    self.music_player = MusicPlayer(Paths.tmp_audio, self.music_player.playing, self.scrub_bar.current_time)
                    # self.sound_wave = SoundWave(self.sound_wave.rect, faded_song_data, sample_rate)
                    # self.equalizer = Equalizer(self.equalizer.rect, faded_song_data, sample_rate)
                    # self.scrub_bar = ScrubBar(self.scrub_bar.rect, faded_song_data, sample_rate)

    def draw(self):
        self.window.fill(Colors.background)

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
        fade_dur = self.fade_time
        total_frames = int(dur * self.render_framerate)
        out_path = (Paths.video_output / self.song_path.name).with_suffix(".mp4")

        # deleting old images
        for f in Paths.images.iterdir():
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

            file_path = Paths.images / f"{frame_num:05d}.bmp"
            pygame.image.save(surface, file_path)
            time_pos += 1/self.render_framerate
            frame_num += 1
        
        print(f"\nstitching together")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(self.render_framerate),
            "-start_number", "0",
            "-i", str(Paths.images)+r"/%05d.bmp",
            "-ss", str(start),
            "-t", str(dur),
            "-i", str(self.song_path),
            "-af", f"afade=t=in:st=0:d={fade_dur},afade=t=out:st={dur-fade_dur}:d={fade_dur}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-r", str(self.render_framerate),
            str(out_path)
        ]

        print(f"ffmpeg command:\n{' '.join(cmd)}")

        subprocess.run(cmd)

        print(f"done rendering! video is at {out_path.absolute()}")

    def fade(self):
        fade_in = np.linspace(0,1,self.fade_samples)[:, np.newaxis]
        fade_out = np.linspace(1,0,self.fade_samples)[:, np.newaxis]
        fade_in_start = int(self.scrub_bar.start_pos * self.sample_rate)
        fade_out_start = int(self.scrub_bar.end_pos * self.sample_rate - self.fade_samples)
        faded_song = self.song_data.copy()
        faded_song[:fade_in_start, :] = 0
        faded_song[fade_out_start+self.fade_samples:, :] = 0
        faded_song[fade_in_start:fade_in_start+self.fade_samples, :] *= fade_in
        faded_song[fade_out_start:fade_out_start+self.fade_samples, :] *= fade_out
        sf.write(Paths.tmp_audio, faded_song, self.sample_rate)
