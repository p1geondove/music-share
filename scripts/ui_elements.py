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
    def __init__(self, pos:tuple[int,int]|pygame.Vector2, text:str = '', background = False, font = None):
        if isinstance(pos, tuple):
            self.pos = int(pos[0]), int(pos[1])
        elif isinstance(pos, pygame.Vector2):
            self.pos = int(pos.x), int(pos.y)
        else:
            self.pos = 0, 0
        if font is None:
            self.font = Fonts.medium
        else:
            self.font = font
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
            pygame.draw.rect(self.surface, Colors.text_background, self.rect, 2, 3)

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

            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.active:
                    self.active = False
                    self.draw()
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
    def __init__(self, pos:tuple[int,int], txt:str, checkbox=True, font_size = 24) -> None:
        self.pos = pos # position of the element
        self.show_checkbox = checkbox # bool to determine if checkbox is being drawn

        pos_textbox = pos[0]+Sizes.meta_tag_margin, pos[1]+Sizes.meta_tag_margin # position relative to self.surface
        font = Fonts.custom(font_size)
        self.textbox = TextField(pos_textbox, txt, font=font) # texfield element

        height = self.textbox.rect.height # abundant variable for easier reading
        rect_checkbox = pygame.Rect(self.textbox.rect.right + Sizes.meta_tag_padding, Sizes.meta_tag_margin + pos[1], height, height) # calculate where checkbox is inside self.surface
        self.checkbox = CheckBox(rect_checkbox) # checkbox element

        self.draw() # self.surface emerges here

    def get_surface_size(self):
        inner_size_x, inner_size_y = self.textbox.rect.size # first get the size of the elements
        if self.show_checkbox: # if were also rendering checkbox
            inner_size_x += Sizes.meta_tag_padding + self.checkbox.rect.width # grow x size by checkbox and padding
        surface_size = inner_size_x + 2*Sizes.meta_tag_margin, inner_size_y + 2*Sizes.meta_tag_margin # lastly add the fade margin
        return (inner_size_x, inner_size_y), surface_size
    
    def render_background(self, elements_size:tuple[int,int], surface_size:tuple[int,int]):
        surface = pygame.Surface(surface_size, pygame.SRCALPHA) # make a new surface for the background
        inner_pos = Sizes.meta_tag_margin, Sizes.meta_tag_margin # position for the constant color rect
        pygame.draw.rect(surface, Colors.background_music_elements, (inner_pos, elements_size)) # draw constant color
        colors = [Colors.background_music_elements.lerp((0,0,0,0),x/(Sizes.meta_tag_margin+1)) for x in range(1,Sizes.meta_tag_margin+1)] # calculate colors used for fade

        for x,c in enumerate(colors,1): # loop over relative position and color
            inv = Sizes.meta_tag_margin - x # invert the distance
            rsize = surface_size[0]-2*inv, surface_size[1]-2*inv # rect size
            pygame.draw.rect(surface, c, ((inv, inv), rsize), 1, x) # draw rounded rect with size and color
        
        return surface

    def draw(self):
        elements_size, surface_size = self.get_surface_size() # calculate how big the surface is
        self.surface = pygame.Surface(surface_size, pygame.SRCALPHA) # reset self.surface to new size
        background = self.render_background(elements_size, surface_size) # get background

        self.surface.blit(background) # blit background
        self.surface.blit(self.textbox.surface, (Sizes.meta_tag_margin,Sizes.meta_tag_margin)) # blit textfield to self.surface

        if self.show_checkbox: # if we draw checkbox
            checkbox_x = Sizes.meta_tag_margin + self.textbox.rect.width + Sizes.meta_tag_padding # calculate x pos next to the nex
            checkbox_pos = checkbox_x, Sizes.meta_tag_margin # put x and y pos into tuple
            self.surface.blit(self.checkbox.surface, checkbox_pos) # blit checkbox to self.surface

    def handle_event(self, event:pygame.Event):
        updated = False # variable if either texfield of checkbox changed

        if self.textbox.handle_event(event): # if textfield changed
            self.checkbox.rect.x = self.textbox.rect.right + Sizes.meta_tag_padding # change x position of checkbox (only for global click/handle_event, not drawing)
            updated = True # check update flag

        if self.checkbox.handle_event(event): # if checkbox changed
            updated = True # check update flag

        if updated: # if update flag checked
            self.draw() # redraw everything
