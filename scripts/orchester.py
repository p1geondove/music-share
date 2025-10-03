import sys
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path

import pygame

from .const import Colors, Fonts, Paths, Sizes, Positions
from .helpers import get_metadata, time_to_str, str_to_time
from .ui_elements import CheckBox, MetadataTag, TextField
from .audio_elements import MusicPlayer, SoundWave, ScrubBar, Equalizer

class Orchestrator:
    def __init__(self, window:pygame.Surface, song_path:Path|None = None) -> None:
        self.window = window
        self.surface_cover = pygame.Surface(self.window.size, pygame.SRCALPHA)
        self.surface_info = pygame.Surface(self.window.size, pygame.SRCALPHA)
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
        else:
            self.song_mono = self.song_data.copy()
        self.song_mono = np.clip(self.song_mono, -1, 1)

        # create a music player
        self.music_player = MusicPlayer(song_path, self.playing)

        # create sound wave top
        self.draw_info("Setting up sound_wave")
        self.sound_wave = SoundWave(
            Positions.soundwave,
            self.song_mono,
            self.sample_rate
        )

        # create a scrub bar bottom left
        self.draw_info("Setting up scrub bar")
        self.scrub_bar = ScrubBar(
            Positions.scrubbar,
            self.song_mono,
            self.sample_rate
        )

        # create equalizer bottom right
        self.draw_info("Setting up equalizer")
        self.equalizer = Equalizer(
            Positions.equalizer,
            self.song_mono,
            self.sample_rate,
        )

        # put all the metadata in MetadataTags
        self.tags:list[MetadataTag] = []
        for y, (meta_type, value) in enumerate(self.metadata.items()):
            if meta_type in {"cover_art", "cover_art_blur"}:
                continue
            y_pos = self.sound_wave.rect.bottom + y * (Fonts.medium.get_height() + Sizes.meta_tag_padding)
            x_pos = Sizes.meta_tag_padding
            text = f"{meta_type}: {value}"
            self.tags.append(MetadataTag((x_pos, y_pos), text))

        # textfield for start / end fade (wont get rendered)
        self.start_fade_box = TextField(Positions.start_fade_textfield, time_to_str(0), True)
        self.end_fade_box = TextField(Positions.end_fade_textfield, time_to_str(self.scrub_bar.end_pos), True)
        self.current_time_box = TextField(Positions.current_time_textfield, time_to_str(0), True)

        # checkbox can toggles clipper
        self.clipper_checkbox = CheckBox(Positions.clipper_checkbox, True)

        # say that its fully initialized
        self.initialized = True

    def convert_cover(self):
        """ loads the cover art from metadata and adjusts size, or prints text that no cover has been found """
        if not self.metadata["cover_art"]:
            self.surface_cover.fill(Colors.background)
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
        # --- handle events, initialized or not ---

        # quit wgen pressing X
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)

        # quick when pressing ESC
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

        # make whole new orchester when drag-dropping a new file
        elif event.type == pygame.DROPFILE:
            path = Path(event.file)
            if self.initialized and path.suffix in (".jpg", ".jpeg", ".bmp", ".png", ".gif"):
                self.metadata["cover_art"] = pygame.image.load(path)
                self.convert_cover()
            else:
                return Orchestrator(self.window, Path(event.file))

        # --- handle only these events when initialized ---
        if not self.initialized:
            return

        # handle text and checkbox from metadata tags, and also check if were typing
        typing = False
        for t in self.tags:
            t.handle_event(event)
            typing = typing or t.textbox.active

        if event.type == pygame.KEYDOWN:
            # check if pressing r or space, but not when writing in metadata textfield
            if event.key == pygame.K_SPACE and not typing:
                self.playing = not self.playing
                if self.playing:
                    self.music_player.resume()
                else:
                    self.music_player.pause()

            elif event.key == pygame.K_r and not typing:
                self.render()

        # change scrub_bar when current_time_box changes
        if "text_changed" in self.current_time_box.handle_event(event):
            time_pos = str_to_time(self.current_time_box.text)
            if time_pos:
                self.scrub_bar.current_time = time_pos
                self.music_player.play_from_position(time_pos)

        # change scrub_bar when start_fade_box changes
        if "text_changed" in self.start_fade_box.handle_event(event):
            time_pos = str_to_time(self.start_fade_box.text)
            if time_pos:
                self.scrub_bar.start_pos = time_pos
                self.fade()

        # change scrub_bar when end_fade_box changes
        if "text_changed" in self.end_fade_box.handle_event(event):
            time_pos = str_to_time(self.end_fade_box.text)
            if time_pos:
                self.scrub_bar.end_pos = time_pos
                self.fade()

        # toggle clipper in scrubbar according to clipper checkbox
        if self.clipper_checkbox.handle_event(event):
            self.sound_wave.clipping_enabled = not self.sound_wave.clipping_enabled

        # handle scrubbar
        if (special_events:=self.scrub_bar.handle_event(event)):
            for special_event in special_events:
                # change current_time_box when scrub_bar changes
                if special_event == "playing_pos changed":
                    self.music_player.play_from_position(self.scrub_bar.current_time)
                    self.current_time_box.text = time_to_str(self.scrub_bar.current_time)
                    self.current_time_box.draw()
                    #print(self.current_time_box.text)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 3:
                        # change start_fade_box when scrub_bar.start_pos changed
                        if special_event == "start_pos changed":
                            self.start_fade_box.text = time_to_str(self.scrub_bar.start_pos)
                            self.start_fade_box.draw()
                            self.fade()

                        # change end_fade_box when scrub_bar.end_pos changes
                        elif special_event == "end_pos changed":
                            self.end_fade_box.text = time_to_str(self.scrub_bar.end_pos)
                            self.end_fade_box.draw()
                            self.fade()

    def draw(self):
        self.window.fill(Colors.background)

        if not self.initialized:
            self.window.blit(self.surface_info)
            return

        time_pos = self.music_player.get_current_position()
        #print(f"{time_pos = }")
        #print(f"{self.equalizer.eq_data = }")
        self.scrub_bar.current_time = time_pos
        if self.music_player.playing:
            self.current_time_box.text = time_to_str(time_pos)
            self.current_time_box.draw()

        blits_info = [
            (self.surface_cover, (0,0)),
            self.scrub_bar.draw(),
            self.sound_wave.draw(time_pos),
            self.equalizer.draw(time_pos),
            (self.current_time_box.surface, self.current_time_box.pos),
            (self.start_fade_box.surface, self.start_fade_box.pos),
            (self.end_fade_box.surface, self.end_fade_box.pos),
            (self.clipper_checkbox.surface, self.clipper_checkbox.rect.topleft),
        ]

        blits_info.extend([(t.surface, t.pos) for t in self.tags])

        self.window.blits(blits_info)

    def render(self):
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
        fade_in_start = int(self.scrub_bar.start_pos * self.sample_rate)
        fade_out_start = int(self.scrub_bar.end_pos * self.sample_rate - self.fade_samples)
        faded_song = self.song_data.copy()

        if self.num_channels > 1:
            fade_in = np.linspace(0,1,self.fade_samples)[:, np.newaxis]
            fade_out = np.linspace(1,0,self.fade_samples)[:, np.newaxis]
            faded_song[:fade_in_start, :] = 0
            faded_song[fade_out_start+self.fade_samples:, :] = 0
            faded_song[fade_in_start:fade_in_start+self.fade_samples, :] *= fade_in
            faded_song[fade_out_start:fade_out_start+self.fade_samples, :] *= fade_out
        else:
            fade_in = np.linspace(0,1,self.fade_samples)
            fade_out = np.linspace(1,0,self.fade_samples)
            faded_song[:fade_in_start] = 0
            faded_song[fade_out_start+self.fade_samples:] = 0
            faded_song[fade_in_start:fade_in_start+self.fade_samples] *= fade_in
            faded_song[fade_out_start:fade_out_start+self.fade_samples] *= fade_out

        sf.write(Paths.tmp_audio, faded_song, self.sample_rate)
        self.music_player = MusicPlayer(Paths.tmp_audio, self.music_player.playing, self.scrub_bar.current_time)
