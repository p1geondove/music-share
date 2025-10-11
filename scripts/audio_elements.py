import time
from pathlib import Path

import pygame
import numpy as np

from .const import Colors, Sizes, SVGs, PositionsConst

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

    def toggle_pause(self):
        if self.playing:
            self.pause()
        else:
            self.resume()

    def set_song(self, song_path:Path):
        pygame.mixer_music.load(song_path)
        self.beginnig = time.time()
        self.playing = True
        pygame.mixer_music.play()

class ScrubBar:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int) -> None:
        self.song_data = song_data
        self.sample_rate = sample_rate
        self.song_length = len(song_data) / sample_rate

        self.current_time = 0.0
        self.start_pos = 0.0
        self.end_pos = self.song_length
        self.pressed_left = False
        self.pressed_right = False

        self.resize(rect)

    def render_background(self):
        self.background = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        fade_size = int(Sizes.background_fade * self.rect.height)
        height_constant_color = self.rect.height - fade_size
        fade_rect = (0, fade_size, self.rect.width, height_constant_color)
        pygame.draw.rect(self.background, Colors.background_music_elements, fade_rect)

        alpha_values = np.linspace(0, Colors.background_music_elements.a, fade_size, dtype=int)
        y_positions = range(fade_size + 1)

        for alpha, ypos in zip(alpha_values, y_positions):
            pygame.draw.line(self.background, (0,0,0,alpha), (0,ypos), (self.rect.right,ypos))

    def calc_amplitudes(self):
        self.bar_width = self.rect.width / Sizes.amount_bars - Sizes.bar_padding
        self.bar_radius = self.bar_width / 2
        self.x_positions = np.linspace(Sizes.bar_padding/2, self.rect.width - self.bar_width - Sizes.bar_padding, Sizes.amount_bars, dtype=int)

        # Compute true time boundaries from audio
        total_samples = len(self.song_data)
        samples_per_bar = total_samples / Sizes.amount_bars  # keep as float for accuracy
        self.bar_time_starts = np.arange(Sizes.amount_bars) * (samples_per_bar / self.sample_rate)
        self.bar_time_ends = self.bar_time_starts + (samples_per_bar / self.sample_rate)
        self.bar_time_ends[-1] = self.song_length

        # compute amplitudes from actual audio blocks
        indices = np.linspace(0, total_samples, Sizes.amount_bars + 1, dtype=int)
        blocks = [self.song_data[indices[i]:indices[i+1]] for i in range(Sizes.amount_bars)]
        amp = np.array([np.mean(np.abs(b)) if len(b) > 0 else 0 for b in blocks])
        amp = amp / np.max(amp) if np.max(amp) > 0 else amp
        fade_size = self.rect.height * Sizes.background_fade
        height = self.rect.height - fade_size
        self.amplitude = (fade_size + height - height * amp).astype(int)

    def draw(self) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        surface.blit(self.background, (0,0))

        for i, (x_pos, amp) in enumerate(zip(self.x_positions, self.amplitude)):
            bar_time_start = self.bar_time_starts[i]
            bar_time_end = self.bar_time_ends[i]
            height = self.rect.height - amp

            # full bar (playhead highlight)
            lerp_val = min(max(0, (self.current_time - bar_time_start) / (bar_time_end - bar_time_start)), 1)
            color_bar = pygame.Color.lerp(Colors.bar_dim, Colors.bar_bright, lerp_val)
            pygame.draw.rect(surface, color_bar, (x_pos, amp, self.bar_width, height))
            pygame.draw.circle(surface, color_bar, (x_pos + self.bar_radius, amp), self.bar_radius)

            # fade regions (start/end)
            if not (self.start_pos <= bar_time_start and bar_time_end <= self.end_pos):
                if bar_time_start < self.start_pos < bar_time_end:
                    lerp_val = (bar_time_end - self.start_pos) / (bar_time_end - bar_time_start)
                    color_fade = pygame.Color.lerp(Colors.bar_dark, color_bar, lerp_val)
                elif bar_time_start < self.end_pos < bar_time_end:
                    lerp_val = (self.end_pos - bar_time_start) / (bar_time_end - bar_time_start)
                    color_fade = pygame.Color.lerp(Colors.bar_dark, color_bar, lerp_val)
                else:
                    color_fade = Colors.bar_dark

                pygame.draw.rect(surface, color_fade, (x_pos, (self.rect.height + amp) // 2, self.bar_width, height // 2))

        return surface, self.rect.topleft

    def handle_event(self, event:pygame.Event):
        def check_fade_pos():
            x_loacle = int(event.pos[0]) - self.rect.left
            song_pos = min(max(0,x_loacle / self.rect.width * self.song_length), self.song_length)
            deltas = (abs(self.start_pos - song_pos), abs(self.end_pos - song_pos))

            if deltas[0] < deltas[1]:
                self.start_pos = song_pos
                special_events.append("start_pos changed")
            else:
                self.end_pos = song_pos
                special_events.append("end_pos changed")

        def check_playing_pos():
            x_loacle = int(event.pos[0]) - self.rect.left
            self.current_time = min(max(0,x_loacle / self.rect.width * self.song_length), self.song_length)
            special_events.append("playing_pos changed")

        special_events = []

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 1: # left mouse button pressed
                    self.pressed_left = True
                    check_playing_pos()

                elif event.button == 3: # righ mouse button pressed
                    self.pressed_right = True
                    check_fade_pos()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # left mouse button released
                self.pressed_left = False

            elif event.button == 3: # right mouse button released
                if self.pressed_right:
                    check_fade_pos()
                self.pressed_right = False

        if event.type == pygame.MOUSEMOTION:
            if self.pressed_left: # scrub along the time axis
                check_playing_pos()

            elif self.pressed_right: # scrub the start or end positions
                check_fade_pos()

        return special_events

    def resize(self, rect:pygame.Rect):
        self.rect = rect
        self.render_background()
        self.calc_amplitudes()

    def copy(self, rect:pygame.Rect):
        new_scrubbar = object.__new__(ScrubBar)
        new_scrubbar.song_data = self.song_data.copy()
        new_scrubbar.sample_rate = self.sample_rate
        new_scrubbar.song_length = self.song_length
        new_scrubbar.current_time = self.current_time
        new_scrubbar.start_pos = self.start_pos
        new_scrubbar.end_pos = self.end_pos
        new_scrubbar.resize(rect)
        return new_scrubbar

class SoundWave:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int) -> None:
        self.song_data_raw = song_data
        self.sample_rate = sample_rate
        self.song_length = len(song_data) / sample_rate
        self.clipping_data = np.abs(song_data) > 0.99
        self.clipping_img = SVGs.clip
        self.clipping_enabled = True
        self.resize(rect)

    def render_background(self):
        self.background = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        fade_size = int(Sizes.background_fade * self.rect.height)
        height_constant_color = self.rect.height - fade_size
        rect = (0, 0, self.rect.width, height_constant_color)
        pygame.draw.rect(self.background, Colors.background_music_elements, rect)
        alpha_values = np.linspace(Colors.background_music_elements.a, 0, fade_size, dtype=int)
        y_positions = range(height_constant_color, self.rect.height+1)

        for alpha, ypos in zip(alpha_values, y_positions):
            pygame.draw.line(self.background, (0,0,0,alpha), (0,ypos), (self.rect.right,ypos))

    def draw(self, position:float) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        surface.blit(self.background, (0,0))

        start_pos = min(int(position * self.sample_rate), self.song_data.size - Sizes.soundwave_samples - 1)
        samples = self.song_data[start_pos : start_pos + Sizes.soundwave_samples]
        x_pos = np.arange(samples.size) * surface.width / Sizes.soundwave_samples
        points = np.stack((x_pos, samples), axis=1)
        pygame.draw.lines(surface, Colors.wave, False, points)

        if np.any(self.clipping_data[start_pos : start_pos + Sizes.soundwave_samples]) and self.clipping_enabled:
            surface.blit(self.clipping_img, PositionsConst.clipper)

        return surface, self.rect.topleft
    
    def resize(self, rect:pygame.Rect):
        self.rect = rect
        self.render_background()
        self.song_data = (self.song_data_raw + 1) / 2 * (self.rect.height - Sizes.background_fade * self.rect.height) # normalize and scale (-1, 1) to (0, height-background_fade)

    def copy(self, rect:pygame.Rect):
        new_soundwave = object.__new__(SoundWave)
        new_soundwave.rect = rect
        new_soundwave.song_data_raw = self.song_data_raw.copy()
        new_soundwave.song_data = self.song_data.copy()
        new_soundwave.sample_rate = self.sample_rate
        new_soundwave.song_length = self.song_length
        new_soundwave.clipping_data = self.clipping_data.copy()
        new_soundwave.clipping_img = self.clipping_img.copy()
        new_soundwave.clipping_enabled = self.clipping_enabled
        new_soundwave.resize(rect)
        return new_soundwave

class Equalizer:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int):
        self.rect = rect
        self.sample_rate = sample_rate

        # fft constants
        self.freq_bands = np.geomspace(Sizes.fft_low_freq, Sizes.fft_high_freq, Sizes.amount_bars)
        self.amount_windows = (len(song_data) - Sizes.fft_window_size) // Sizes.fft_hop_size + 1
        bin_freqs = np.fft.rfftfreq(Sizes.fft_window_size, 1/sample_rate)
        target_bins = [np.argmin(np.abs(bin_freqs - f)) for f in self.freq_bands]
        self.eq_data_raw = np.zeros((self.amount_windows, len(self.freq_bands)))

        # calculate fft
        for i in range(self.amount_windows):
            start = i * Sizes.fft_hop_size
            end = start + Sizes.fft_window_size
            window = song_data[start:end] * np.blackman(Sizes.fft_window_size)
            fft = np.fft.rfft(window)
            self.eq_data_raw[i,:] = np.abs(fft[target_bins])

        self.resize(self.rect)

    def render_background(self):
        self.background = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.background.fill(Colors.background_music_elements)

    def resize(self, rect:pygame.Rect):
        self.rect = rect
        self.eq_data = np.log10(self.eq_data_raw + 1e-10) # log that bish
        self.eq_data = np.clip(self.eq_data / np.max(self.eq_data),0,1) * rect.height # normalize and scale to surface
        self.bar_width = rect.width / len(self.freq_bands) - Sizes.bar_padding
        self.bar_radius = self.bar_width / 2
        self.x_positions = np.linspace(Sizes.bar_padding/2, rect.width-self.bar_width-Sizes.bar_padding, Sizes.amount_bars, dtype=int)
        self.render_background()

    def draw(self, position:float) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        surface.blit(self.background, (0,0))
        frame_index = min(int(position * self.sample_rate / Sizes.fft_hop_size), self.amount_windows-1)
        eq_data = self.eq_data[frame_index]

        for x, val in zip(self.x_positions, eq_data):
            pygame.draw.circle(surface, Colors.bar_bright, (x+self.bar_radius,val), self.bar_radius)
            pygame.draw.rect(surface, Colors.bar_bright, (x,0,self.bar_width,val))

        return surface, self.rect.topleft
    
    def copy(self, rect:pygame.Rect):
        new_eq = object.__new__(Equalizer)
        new_eq.sample_rate = self.sample_rate
        new_eq.freq_bands = self.freq_bands.copy()
        new_eq.amount_windows = self.amount_windows
        new_eq.eq_data_raw = self.eq_data_raw.copy()
        new_eq.rect = rect
        new_eq.resize(rect)
        return new_eq
