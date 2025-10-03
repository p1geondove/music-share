import string

import pygame

from .const import Colors, Fonts, Sizes

class CheckBox():
    def __init__(self, rect:pygame.Rect, checked:bool = False, background = True) -> None:
        self.rect = rect
        #self.pos = list(pos)
        #self.size = int(size)
        self.checked = bool(checked)
        self.checkmark = self.render_checkmark()
        self.hover = False
        self.draw_background = bool(background)
        self.draw()

    def render_checkmark(self):
        checkmark_points = [
            pygame.Vector2(.09, .6),
            pygame.Vector2(.4,  .9),
            pygame.Vector2(.9,  .1)
        ]
        scaled_points = [self.rect.height * p for p in checkmark_points]
        checkmark_width = int(self.rect.height * 0.15)
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.lines(surface, Colors.checkbox_checkmark, False, scaled_points, checkmark_width)
        return surface

    def draw(self):
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        if self.draw_background:
            pygame.draw.rect(self.surface, Colors.background, ((0,0), self.rect.size), 0, Sizes.checkbox_radius)

        pygame.draw.rect(self.surface, Colors.checkbox_border, ((0,0), self.rect.size), Sizes.checkbox_width, Sizes.checkbox_radius)

        if self.checked:
            self.surface.blit(self.checkmark, (0,0))

    def handle_event(self, event:pygame.Event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.hover:
                self.checked = not self.checked
                self.draw()
                return True

class TextField():
    def __init__(self, pos:tuple[int,int]|pygame.Vector2, text:str = '', background = False):
        if isinstance(pos, tuple):
            self.pos = int(pos[0]), int(pos[1])
        elif isinstance(pos, pygame.Vector2):
            self.pos = int(pos.x), int(pos.y)
        else:
            self.pos = 0, 0
        self.font = Fonts.medium
        self.active = False
        self.text = str(text)
        self.hover = False
        self.selection = None
        self.cursorspos = 0
        self.pressed = False
        self.draw_background = bool(background)

        self.draw()

    def get_rect(self):
        txt = self.font.render(self.text, False, "black")
        size_y = self.font.get_height()
        size_x = max(self.font.size("a")[0], txt.width)
        self.rect = pygame.Rect(self.pos, (size_x,size_y))
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

    def draw(self, draw_border=True):
        self.get_rect()
        color_text = Colors.text
        text = self.font.render(self.text, True, Colors.text)

        if self.draw_background:
            self.surface.fill(Colors.background)

        if self.selection:
            before_selection = self.text[:self.selection[0]]
            selected_text = self.text[self.selection[0]:self.selection[1]]
            selection_size = self.font.size(selected_text)
            selection_pos = self.font.size(before_selection)[0], 0
            pygame.draw.rect(self.surface, Colors.text_selection, (selection_pos, selection_size), 0, 3)

        if self.active:
            cursor_x = self.font.size('a')[0] * self.cursorspos
            pygame.draw.rect(self.surface, color_text, (cursor_x, 2, 1, text.height-4)) # cursror line

        if draw_border:
            pygame.draw.rect(self.surface, Colors.text_border, self.rect, 2, 3)

        self.surface.blit(text, (0,0))

    def handle_event(self, event:pygame.Event):
        special_events:list[str] = []

        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.hover = event.pos
                if self.pressed:
                    pos1 = self.cursorspos
                    pos2 = int((event.pos[0] - self.pos[0]) / self.font.size("a")[0])
                    self.selection = sorted((pos1, pos2))
                    self.draw()
                    special_events.append("draw")
                if not self.hover:
                    self.draw()
                    special_events.append('draw')
            else:
                self.hover = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.active = bool(self.hover)
                if self.active:
                    self.cursorspos = int((event.pos[0] - self.pos[0]) / self.font.size("a")[0])
                    self.pressed = True
                    self.selection = None
                if not self.active: self.selection = None
                self.draw()
                special_events.append('draw')

        elif event.type == pygame.MOUSEBUTTONUP:
            self.pressed = False

        elif event.type == pygame.KEYDOWN and self.active: # pressing keyboard while its active
            if event.key == pygame.K_BACKSPACE: # backspace = delete char left to the cursor or entire selection
                if self.selection: # somthing is selected
                    self.text = self.text[:self.selection[0]] + self.text[self.selection[1]:]
                    self.cursorspos = self.selection[0]
                    self.selection = None

                elif self.cursorspos > 0: # check if the cursor is full left or has chars it can remove
                    if pygame.key.get_pressed()[pygame.K_LCTRL]: # if we press ctrl delete entire word
                        next_pos = self.next_char(0)
                        self.text = self.text[:next_pos] + self.text[self.cursorspos:]
                        self.cursorspos = next_pos

                    else: # no selection, no ctrl presse = remove char left to the cursor
                        self.text = self.text[:self.cursorspos-1] + self.text[self.cursorspos:]
                        self.cursorspos -= 1

                self.draw()
                special_events.append('draw')
                special_events.append('text_changed')

            elif event.key == pygame.K_DELETE: # del key removes right of the cursors
                if self.selection: # check if theres anything selected
                    self.text = self.text[:self.selection[0]] + self.text[self.selection[1]:]
                    self.cursorspos = self.selection[0]
                    self.selection = None
                elif pygame.key.get_pressed()[pygame.K_LCTRL]: # check if were pressing ctrl key, to remove whole word
                    self.text = self.text[:self.cursorspos] + self.text[self.next_char(1):]
                else: # no ctrl, no selection, just delete the char right to the cursor
                    self.text = self.text[:self.cursorspos] + self.text[self.cursorspos + 1:]

                self.draw()
                special_events.append('draw')
                special_events.append('text_changed')

            elif event.key == pygame.K_RETURN:
                special_events.append('textfield_return')

            elif event.key == pygame.K_LEFT:
                start_pos = self.cursorspos
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.cursorspos = self.next_char(0)
                else:
                    self.cursorspos -= 1

                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    if self.selection:
                        if start_pos == self.selection[1]:
                            self.selection[1] = self.cursorspos
                        else:
                            self.selection[0] = self.cursorspos
                    else:
                        self.selection = [self.cursorspos, start_pos]
                elif self.selection:
                    self.cursorspos = self.selection[0]
                    self.selection = None

                self.cursorspos = min(max(self.cursorspos, 0), len(self.text))
                if self.selection:
                    if self.selection[0] == self.selection[1]:
                        self.selection = None

                self.draw()
                special_events.append('draw')

            elif event.key == pygame.K_RIGHT: # literal copy of left with a bunch of bits flipped
                start_pos = self.cursorspos
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.cursorspos = self.next_char(1)
                else:
                    self.cursorspos += 1

                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    if self.selection:
                        if start_pos == self.selection[0]:
                            self.selection[0] = self.cursorspos
                        else:
                            self.selection[1] = self.cursorspos
                    else:
                        self.selection = [start_pos, self.cursorspos]
                elif self.selection:
                    self.cursorspos = self.selection[1]
                    self.selection = None

                self.cursorspos = min(max(self.cursorspos, 0), len(self.text))
                if self.selection:
                    if self.selection[0] == self.selection[1]:
                        self.selection = None

                self.draw()
                special_events.append('draw')

            elif event.unicode == '\x01': # ctrl + a
                self.selection = [0, len(self.text)]
                self.draw()
                special_events.append('draw')

            elif event.unicode == '\x03': # ctrl + c
                if self.selection:
                    pygame.scrap.put_text(self.text[self.selection[0]:self.selection[1]])
                else:
                    pygame.scrap.put_text(self.text)

            elif event.unicode == '\x16': # ctrl + v
                if self.selection:
                    self.text = self.text[:self.selection[0]] + pygame.scrap.get_text() + self.text[self.selection[1]:]
                    self.cursorspos = self.selection[0]
                    self.selection = None
                else:
                    _text = pygame.scrap.get_text()
                    self.text = self.text[:self.cursorspos] + _text + self.text[self.cursorspos:]
                    self.cursorspos += len(_text)

                self.draw()
                special_events.append('draw')
                special_events.append('text_changed')

            elif event.unicode == '\x18': # ctrl + x
                if self.selection:
                    pygame.scrap.put_text(self.text[self.selection[0]:self.selection[1]])
                    self.text = self.text[:self.selection[0]] + self.text[self.selection[1]:]
                    self.cursorspos = self.selection[0]
                    self.selection = None
                else:
                    pygame.scrap.put_text(self.text)
                    self.text = ''
                    self.cursorspos = 0

                self.draw()
                special_events.append('draw')

            elif event.unicode and event.unicode in string.printable[:-5]:
                if self.selection:
                    self.text = self.text[:self.selection[0]] + event.unicode + self.text[self.selection[1]:]
                    self.cursorspos = self.selection[0]
                    self.selection = None
                else:
                    self.text = self.text[:self.cursorspos] + event.unicode + self.text[self.cursorspos:]

                self.cursorspos += 1
                self.draw()
                special_events.append('draw')
                special_events.append('text_changed')

        if not self.text:
            self.cursorspos = 0

        return special_events

    def resize(self, rect:pygame.Rect|tuple):
        self.rect = pygame.Rect(rect)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.draw()

    def next_char(self, direction:int):
        if direction > 0:
            next_pos = self.text.find(' ',self.cursorspos+1)
            return len(self.text) if next_pos == -1 else next_pos
        else:
            txt = self.text[self.cursorspos-1::-1]
            if not isinstance(txt,str): return 0
            dx = txt.find(' ',1)
            if dx == -1: return 0
            return self.cursorspos - dx

class MetadataTag:
    def __init__(self, pos:tuple[int,int], txt:str) -> None:
        self.pos = pos

        pos_textbox = pos[0]+Sizes.meta_tag_margin, pos[1]+Sizes.meta_tag_margin
        self.textbox = TextField(pos_textbox, txt)

        height = self.textbox.rect.height
        rect_checkbox = pygame.Rect(self.textbox.rect.right + Sizes.meta_tag_padding, Sizes.meta_tag_margin + pos[1], height, height)
        self.checkbox = CheckBox(rect_checkbox)

        self.draw()


    def render_background(self, size:tuple[int,int], margin:int=Sizes.meta_tag_margin):
        self.background = pygame.Surface(size, pygame.SRCALPHA)
        inner_pos = margin, margin
        inner_size = size[0] - 2*margin, size[1] - 2*margin
        pygame.draw.rect(self.background, Colors.background_music_elements, (inner_pos, inner_size))
        colors = [Colors.background_music_elements.lerp((0,0,0,0),x/(margin+1)) for x in range(1,margin+1)]

        for x,c in enumerate(colors,1):
            inv = margin - x
            pos = inv, inv
            rsize = size[0]-2*inv, size[1]-2*inv
            pygame.draw.rect(self.background, c, (pos,rsize), 1, x)

    def draw(self):
        checkbox_x = self.textbox.rect.width + Sizes.meta_tag_margin + Sizes.meta_tag_padding
        checkbox_pos = checkbox_x, Sizes.meta_tag_margin
        surface_size = checkbox_x + self.checkbox.rect.width + Sizes.meta_tag_margin, self.checkbox.rect.height + 2 * Sizes.meta_tag_margin
        background_size = self.textbox.rect.width + 2 * Sizes.meta_tag_margin, self.textbox.rect.height + 2 * Sizes.meta_tag_margin
        self.render_background(background_size)
        self.surface = pygame.Surface(surface_size, pygame.SRCALPHA)
        self.surface.blit(self.background, (0,0))
        self.surface.blit(self.textbox.surface, (Sizes.meta_tag_margin,Sizes.meta_tag_margin))
        self.surface.blit(self.checkbox.surface, checkbox_pos)

    def handle_event(self, event:pygame.Event):
        updated = False
        if self.textbox.handle_event(event):
            self.checkbox.rect.x = self.textbox.rect.right + Sizes.meta_tag_padding
            updated = True

        if self.checkbox.handle_event(event):
            updated = True

        if updated:
            self.draw()

