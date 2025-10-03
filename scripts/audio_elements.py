import time
from pathlib import Path

import pygame
import numpy as np

from .const import Colors, Sizes, SVGs, Positions

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
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int) -> None:
        self.rect = rect
        self.song_data = song_data
        self.sample_rate = sample_rate
        self.song_length = len(song_data) / sample_rate

        self.current_time = 0.0
        self.start_pos = 0.0
        self.end_pos = self.song_length
        self.pressed_left = False
        self.pressed_right = False

        self.calc_amplitudes()
        self.background = self.render_background()

    def render_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        height_constant_color = self.rect.height - Sizes.background_fade
        rect = (0, Sizes.background_fade, self.rect.width, height_constant_color)
        pygame.draw.rect(surface, Colors.background_music_elements, rect)

        alpha_values = np.linspace(0, Colors.background_music_elements.a, Sizes.background_fade, dtype=int)
        y_positions = range(Sizes.background_fade + 1)

        for alpha, ypos in zip(alpha_values, y_positions):
            pygame.draw.line(surface, (0,0,0,alpha), (0,ypos), (self.rect.right,ypos))

        return surface

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
        height = self.rect.height - Sizes.background_fade
        self.amplitude = (Sizes.background_fade + height - height * amp).astype(int)

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

class SoundWave:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int, amount_samples:int = 500) -> None:
        self.rect = rect
        self.sample_rate = sample_rate
        self.amount_samples = amount_samples
        self.song_length = len(song_data) / sample_rate
        self.clipping_data = np.abs(song_data) > 0.99
        self.song_data = (song_data + 1) / 2 * (self.rect.height - Sizes.background_fade) # normalize and scale (-1, 1) to (0, height-background_fade)
        self.clipping_img = SVGs.clip
        self.clipping_enabled = True
        self.background = self.render_background()

    def render_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        height_constant_color = self.rect.height - Sizes.background_fade
        rect = (0, 0, self.rect.width, height_constant_color)
        pygame.draw.rect(surface, Colors.background_music_elements, rect)
        alpha_values = np.linspace(Colors.background_music_elements.a, 0, Sizes.background_fade, dtype=int)
        y_positions = range(height_constant_color, self.rect.height+1)

        for alpha, ypos in zip(alpha_values, y_positions):
            pygame.draw.line(surface, (0,0,0,alpha), (0,ypos), (self.rect.right,ypos))

        return surface

    def draw(self, position:float) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        surface.blit(self.background, (0,0))

        start_pos = min(int(position * self.sample_rate), self.song_data.size - self.amount_samples - 1)
        samples = self.song_data[start_pos : start_pos + self.amount_samples]
        x_pos = np.arange(samples.size) * surface.width / self.amount_samples
        points = np.stack((x_pos, samples), axis=1)
        pygame.draw.lines(surface, Colors.wave, False, points)

        if np.any(self.clipping_data[start_pos : start_pos + self.amount_samples]) and self.clipping_enabled:
            surface.blit(self.clipping_img, Positions.clipper)

        return surface, self.rect.topleft

class Equalizer:
    def __init__(self, rect:pygame.Rect, song_data:np.ndarray, sample_rate:int):
        self.rect = rect
        self.sample_rate = sample_rate

        # fft constants
        freq_bands = np.geomspace(Sizes.fft_low_freq, Sizes.fft_high_freq, Sizes.amount_bars)
        self.amount_windows = (len(song_data) - Sizes.fft_window_size) // Sizes.fft_hop_size + 1
        bin_freqs = np.fft.rfftfreq(Sizes.fft_window_size, 1/sample_rate)
        target_bins = [np.argmin(np.abs(bin_freqs - f)) for f in freq_bands]
        self.eq_data = np.zeros((self.amount_windows, len(freq_bands)))

        # calculate fft
        for i in range(self.amount_windows):
            start = i * Sizes.fft_hop_size
            end = start + Sizes.fft_window_size
            window = song_data[start:end] * np.blackman(Sizes.fft_window_size)
            fft = np.fft.rfft(window)
            self.eq_data[i,:] = np.abs(fft[target_bins])

        # normalize fft
        self.eq_data = np.log10(self.eq_data+1e-10) # log that bish
        self.eq_data = np.clip(self.eq_data / np.max(self.eq_data),0,1) * rect.height # normalize and scale to surface

        # drawing constants
        self.bar_width = rect.width / len(freq_bands) - Sizes.bar_padding
        self.bar_radius = self.bar_width / 2
        self.x_positions = np.linspace(Sizes.bar_padding/2, rect.width-self.bar_width-Sizes.bar_padding, Sizes.amount_bars, dtype=int)
        self.background = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.background.fill(Colors.background_music_elements)

    def draw(self, position:float) -> tuple[pygame.Surface, tuple[int,int]]:
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        surface.blit(self.background, (0,0))
        frame_index = min(int(position * self.sample_rate / Sizes.fft_hop_size), self.amount_windows-1)
        eq_data = self.eq_data[frame_index]

        for x, val in zip(self.x_positions, eq_data):
            pygame.draw.circle(surface, Colors.bar_bright, (x+self.bar_radius,val), self.bar_radius)
            pygame.draw.rect(surface, Colors.bar_bright, (x,0,self.bar_width,val))

        return surface, self.rect.topleft

