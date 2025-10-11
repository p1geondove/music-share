import sys
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path

import pygame

from .const import Colors, Paths, Sizes, AllowedFileTypes
from .helpers import get_metadata, time_to_str, str_to_time, convert_cover, fade_song, get_element_positions
from .ui_elements import CheckBox, MetadataTag, TextField
from .audio_elements import MusicPlayer, SoundWave, ScrubBar, Equalizer

class Orchester:
    def __init__(self, window:pygame.Surface, song_path:Path|None = None, render_state=False) -> None:
        self.window = window
        self.song_path = song_path
        self.render_state = render_state

        self.info_surface = window.copy()
        self.cover_surface = window.copy()
    
        self.music_player:MusicPlayer|None = None
        self.soundwave:SoundWave|None = None
        self.scrubbar:ScrubBar|None = None
        self.equalizer:Equalizer|None = None
        self.tags:list[MetadataTag] = []
        self.resolution_textfield:TextField|None = None
        self.ready = False

        if song_path:
            self.set_song(song_path)

    def draw_info(self, txt:str):
        """ prints text in the middle of the screen """
        if self.render_state:
            return
        self.window.fill(Colors.background)
        txt_surface = pygame.Font.render(pygame.font.SysFont(None,50), txt, True, "grey")
        x = self.window.width/2 - txt_surface.width/2
        y = self.window.height/2 - txt_surface.height/2
        self.window.blit(txt_surface, (x,y))
        pygame.display.flip()

    def set_song(self, song_path:Path):
        if song_path.suffix not in {".mp3", ".wav", ".flac", ".opus"}:
            return
        
        self.song_path = song_path

        if not self.render_state: # dont make a musicplayer if were rendering
            self.draw_info("Setting up Musicplayer")
            self.music_player = MusicPlayer(song_path, False)
        
        self.draw_info("Exctracting metadata")
        self.metadata = get_metadata(song_path)
        self.draw_info("Converting cover")
        self.cover_surface = convert_cover(self.metadata["cover_art"], self.window.size)
        self.draw_info("Reading song")
        self.song_data_full, self.sample_rate = sf.read(song_path)

        self.draw_info("Converting song data")
        amount_channels = 1
        if len(self.song_data_full.shape) > 1:
            amount_channels = self.song_data_full.shape[1]

        if amount_channels > 1:
            self.song_data_mono = np.mean(self.song_data_full, axis=1)
        else:
            self.song_data_mono = self.song_data_full

        positions = get_element_positions(self.window.size)
        self.draw_info("Setting up soundwave")
        self.soundwave = SoundWave(positions["soundwave"], self.song_data_mono, self.sample_rate)
        self.draw_info("Setting up scrubbar")
        self.scrubbar = ScrubBar(positions["scrubbar"], self.song_data_mono, self.sample_rate)
        self.draw_info("Setting up equalizer")
        self.equalizer = Equalizer(positions["eqalizer"], self.song_data_mono, self.sample_rate)

        self.draw_info("Setting up metadata tags")
        self.tags = []
        font_size = int(min(self.window.size) / 25)

        for y, (meta_type, value) in enumerate(self.metadata.items()):
            if meta_type == "cover_art": # dont put cover art as tag
                continue
            y_pos = self.soundwave.rect.bottom + y * (font_size + Sizes.meta_tag_padding)
            x_pos = Sizes.meta_tag_padding
            text = f"{meta_type}: {value}"
            tag = MetadataTag((x_pos, y_pos), text, not self.render_state, font_size)
            self.tags.append(tag)

        if not self.render_state:
            self.draw_info("Setting up controls")
            self.start_fade_box = TextField(positions["start_fade_textfield"], time_to_str(0), True)
            self.end_fade_box = TextField(positions["end_fade_textfield"], time_to_str(self.scrubbar.end_pos), True)
            self.current_time_box = TextField(positions["current_time_textfield"], time_to_str(0), True)
            self.resolution_textfield = TextField(positions["resolution_textfield"], f"{Sizes.window_render[0]}x{Sizes.window_render[1]}", True)
            self.clipper_checkbox = CheckBox(positions["clipper_checkbox"], True)

        # self.music_player.resume()
        self.ready = True

    def fade(self):
        fade_song(
            self.song_data_full,
            self.sample_rate,
            self.scrubbar.start_pos,
            self.scrubbar.end_pos
        )
        self.music_player = MusicPlayer(Paths.tmp_audio, self.music_player.playing, self.scrubbar.current_time)

    def render(self):
        print("starting render")

        surface = pygame.Surface(Sizes.window_render, pygame.SRCALPHA)
        orchester = Orchester(surface, render_state=True)
        fade_surface = surface.copy() # used for fading from/to black and the start/end of clip
        time_pos = self.scrubbar.start_pos
        frame_num = 0
        start = self.scrubbar.start_pos
        end = self.scrubbar.end_pos
        dur = end - start
        fade_dur = Sizes.song_fade_time
        total_frames = int(dur * Sizes.render_framerate)
        out_path = (Paths.video_output / self.song_path.name).with_suffix(".mkv")


        positions = get_element_positions(Sizes.window_render)

        orchester.song_data_full = self.song_data_full
        orchester.cover_surface = convert_cover(self.metadata["cover_art"], Sizes.window_render)
        orchester.soundwave = self.soundwave.copy(positions["soundwave"])
        orchester.scrubbar = self.scrubbar.copy(positions["scrubbar"])
        orchester.equalizer = self.equalizer.copy(positions["eqalizer"])

        # orchester.equalizer = Equalizer(positions["eqalizer"], self.song_data_mono, self.sample_rate)
        # orchester.soundwave = SoundWave(positions["soundwave"], self.song_data_mono, self.sample_rate)
        # orchester.scrubbar = ScrubBar(positions["scrubbar"], self.song_data_mono, self.sample_rate)
    
        idx = 0
        font_size = int(min(Sizes.window_render) / 25)
        for tag in self.tags:
            if not tag.checkbox.checked: continue
            y_pos = orchester.soundwave.rect.bottom + idx * (font_size + Sizes.meta_tag_padding)
            x_pos = Sizes.meta_tag_padding
            tag = MetadataTag((x_pos,y_pos), tag.textbox.text, False, font_size)
            orchester.tags.append(tag)
            idx += 1

        while time_pos < end:
            print(f"rendering frame {frame_num}/{total_frames}", end="\r")
            orchester.scrubbar.current_time = time_pos
            orchester.draw()

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
            time_pos += 1 / Sizes.render_framerate
            frame_num += 1

        print(f"\nstitching together")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(Sizes.render_framerate),
            "-start_number", "0",
            "-i", str(Paths.images)+r"/%05d.bmp",
            "-ss", str(start),
            "-t", str(dur),
            "-i", str(self.song_path),
            "-af", f"afade=t=in:st=0:d={fade_dur},afade=t=out:st={dur-fade_dur}:d={fade_dur}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-r", str(Sizes.render_framerate),
            str(out_path)
        ]

        print(f"ffmpeg command:\n{' '.join(cmd)}")

        subprocess.run(cmd)

        print(f"done rendering! video is at {out_path.absolute()}")

    def handle_event(self, event:pygame.Event):
        # quit wgen pressing X
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)

        # quick when pressing ESC
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

        elif event.type == pygame.DROPFILE:
            path = Path(event.file)
            if path.suffix in AllowedFileTypes.audio:
                self.set_song(Path(event.file))
            elif path.suffix in AllowedFileTypes.image:
                self.cover_surface = convert_cover(path, self.window.size)
        
        if not self.ready:
            return
        
        # handle text and checkbox from metadata tags, and also check if were typing
        typing = False
        for t in self.tags:
            t.handle_event(event)
            typing = typing or t.textbox.active

        if event.type == pygame.KEYDOWN:
            # check if pressing r or space, but not when writing in metadata textfield
            if event.key == pygame.K_SPACE and not typing:
                self.music_player.toggle_pause()

            elif event.key == pygame.K_r and not typing:
                self.render()

        # change scrub_bar when current_time_box changes
        if "text_changed" in self.current_time_box.handle_event(event):
            time_pos = str_to_time(self.current_time_box.text)
            if time_pos:
                self.scrubbar.current_time = time_pos
                self.music_player.play_from_position(time_pos)

        # change scrub_bar when start_fade_box changes
        if "text_changed" in self.start_fade_box.handle_event(event):
            time_pos = str_to_time(self.start_fade_box.text)
            if time_pos:
                self.scrubbar.start_pos = time_pos
                self.fade()

        # change scrub_bar when end_fade_box changes
        if "text_changed" in self.end_fade_box.handle_event(event):
            time_pos = str_to_time(self.end_fade_box.text)
            if time_pos:
                self.scrubbar.end_pos = time_pos
                self.fade()

        # toggle clipper in scrubbar according to clipper checkbox
        if self.clipper_checkbox.handle_event(event):
            self.soundwave.clipping_enabled = not self.soundwave.clipping_enabled

        # handle scrubbar
        if (special_events:=self.scrubbar.handle_event(event)):
            for special_event in special_events:
                # change current_time_box when scrub_bar changes
                if special_event == "playing_pos changed":
                    self.music_player.play_from_position(self.scrubbar.current_time)
                    self.current_time_box.text = time_to_str(self.scrubbar.current_time)
                    self.current_time_box.draw()
                    #print(self.current_time_box.text)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 3:
                        # change start_fade_box when scrub_bar.start_pos changed
                        if special_event == "start_pos changed":
                            self.start_fade_box.text = time_to_str(self.scrubbar.start_pos)
                            self.start_fade_box.draw()
                            self.fade()

                        # change end_fade_box when scrub_bar.end_pos changes
                        elif special_event == "end_pos changed":
                            self.end_fade_box.text = time_to_str(self.scrubbar.end_pos)
                            self.end_fade_box.draw()
                            self.fade()

        if "textfield_return" in self.resolution_textfield.handle_event(event):
            try:
                wanted_x, wanted_y = list(map(int, self.resolution_textfield.text.split("x")))
                Sizes.window_render = wanted_x, wanted_y
                factor = Sizes.window_max_size / max(wanted_x, wanted_y)
                preview_x = int(factor * wanted_x)
                preview_y = int(factor * wanted_y)
                self.resize((preview_x, preview_y))
            except Exception as e:
                print("uncaught exception: ", e)
                raise
                pass
            
    def draw(self):
        if not self.ready and not self.render_state:
            self.draw_info("Drop in audiofile")
            return

        # timepos is determined by scrubbar if rendering otherwise by musicplaywer
        if self.render_state:
            time_pos = self.scrubbar.current_time
        else:
            time_pos = self.music_player.get_current_position()
            self.scrubbar.current_time = time_pos

            if self.music_player.playing:
                self.current_time_box.text = time_to_str(time_pos)
                self.current_time_box.draw()

        blits_info = [
            (self.cover_surface, (0,0)),
            self.soundwave.draw(time_pos),
            self.scrubbar.draw(),
            self.equalizer.draw(time_pos),
        ]

        if not self.render_state:
            blits_info.extend([
                (self.clipper_checkbox.surface, self.clipper_checkbox.rect.topleft),
                (self.current_time_box.surface, self.current_time_box.pos),
                (self.start_fade_box.surface, self.start_fade_box.pos),
                (self.end_fade_box.surface, self.end_fade_box.pos),
                (self.resolution_textfield.surface, self.resolution_textfield.pos)
            ])

        blits_info.extend([(t.surface, t.pos) for t in self.tags])

        self.window.blits(blits_info)

    def resize(self, size:tuple[int, int]):
        pygame.display.set_mode(size, pygame.SRCALPHA)
        positions = get_element_positions(size)
        
        if not self.ready:
            self.cover_surface = convert_cover(None, size)
            return
        
        self.cover_surface = convert_cover(self.metadata["cover_art"], size)

        self.soundwave.resize(positions["soundwave"])
        self.scrubbar.resize(positions["scrubbar"])
        self.equalizer.resize(positions["eqalizer"])
        
        # self.scrubbar.rect = positions["scrubbar"]
        # self.scrubbar.calc_amplitudes()
        # self.scrubbar.render_background()

        # self.soundwave.rect = positions["soundwave"]
        # self.soundwave.render_background()

        # self.equalizer.rect = positions["eqalizer"]
        # self.equalizer.render_background()

        self.current_time_box.pos = positions["current_time_textfield"]
        self.start_fade_box.pos = positions["start_fade_textfield"]
        self.end_fade_box.pos = positions["end_fade_textfield"]
        self.resolution_textfield.pos = positions["resolution_textfield"]
