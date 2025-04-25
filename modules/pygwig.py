'Widgets module -- by Tomatofu'

import sys
import time
import math
import random
from typing import Callable
import pygame as pg
from pygame import mixer as mx
from modules.utils import (
        scientific_notation,
        center_word_on_image,
        math_eval,
        last_index_greater_than_zero,
        image_list,
        element_wise_addition,
        arabic_to_roman,
        render_rect,
        )

# i thought it was just utils (without module.) but since its run from main, I put modules.
# NOTE TO SELF: WHEN TAKING LISTS AS PARAMETERS, USE .COPY()!!!!!!!! OR TURN IT INTO A NEW LIST!!!! IT FIXES MOST PROBLEMS!!!
# NOTE TO SELF: DO NOT USE THE BUILTIN TOUCHPAD SUPPORT!!!! IT SUCKS!!!

type image_dict = dict(str=pg.Surface)

class Button(object):

    'Main Button class.'

    def __init__(self: object, 
                 game: object,
                 clickable: int or bool,
                 pos: list or tuple,
                 images: image_dict,
                 size: list or tuple=[],
                 code: str='',
                 scroll: list or tuple=[],
                 resize: list or tuple=[0.1, 0.2]) -> None:

        'The initialization function of the Button class.\n\n' \
        '   game: object (required)\n' \
        '     the game object of the button. can be referred to in the button\'s click code\n' \
        '   clickable: int or bool (required)\n' \
        '     a bool that tells whether the button should be clickable.\n' \
        '     the clickability can be set through the clickable attribute\n' \
        '   pos: list or tuple[int or float] (required)\n' \
        '     the starting position of the button in format (x, y)\n' \
        '     if x or y is a string, then it will be centered on that axis:\n' \
        '       it has two arguments: the screen width to center to, and the pixel ratio\n' \
        '       arguments are split by semicolons (;)\n' \
        '       E.g. "640;1"\n' \
        '   images: dict(str=pygame.Surface) (required)\n' \
        '     the images for the button. accepts three images max, but "image" is required:\n' \
        '       "image:" the normal image for the button\n' \
        '       "hover_image:" the image that displays when the button is hovered over\n' \
        '       "unclickable_image:" the image that displays when the button is unclickable\n' \
        '   size: list or tuple[int or float] (not required)\n' \
        '     the size of the button in format (width, height).\n' \
        '     this is the size used for calculations when resizing\n' \
        '   code: str or code object (not required)\n' \
        '     the code run when the button is clicked. it is run with the exec() function\n' \
        '   scroll: list or tuple (not required)\n' \
        '     the mouse scroll settings of the button. it is a list containing 5 options\n' \
        '       0. the range of x-axis scrolling in format (max increase, max decrease)\n' \
        '       1. the range of y-axis scrolling in format (max increase, max decrease)\n' \
        '       2. the pixel ratio. the scroll will only land on multiples of this value.\n' \
        '          this can be used for pixel art.\n' \
        '       3. the scroll speed\n' \
        '       4. the scroll rectangle. if the mouse is in this rect, then scrolling is allowed.\n' \
        '          if it is 0, then scrolling will always be allowed.\n' \
        '   resize: list or tuple[int or float] (not required)\n' \
        '     the resize settings for the button in format (size increase when hovered, size increase when clicked)'

        self.code = code
        self.clickable = clickable
        self.game = game
        self.scroll_opts = list(scroll) 
        # shallow copy; don't need deepcopy; using list() is the best way because it also works w/ tuples
        self.size = list(size) if size else images['image'].get_size()
        # using class attribute because it is after it is processed
        self.render_size = list(self.size)
        self.pos = []
        size = images['image'].get_size()
        for dex, position in enumerate(pos):
            if type(position) == str:
                # if it is a string, then it will center
                # arguments are split with semicolons
                # the first argument is the width of the screen
                # the second is the pixel ratio
                split_pos = tuple((int(item) for item in position.split(';')))
                self.pos.append(int((split_pos[0] - size[dex]) / 2 // split_pos[1] * split_pos[1]))
            else:
                self.pos.append(position)
        self.render_pos = list(self.pos)

        self.resize_opts = list(resize)
        if scroll:
            self.wanted_scroll_pos = list(pos)
        self.rect = pg.Rect(self.pos[0], self.pos[1],
                            self.size[0], self.size[1])
        self.images = images.copy()
        # Checks for images; if it's not there, it sets it as the default
        # .get() checks if the value exists; if it does, then it returns the value
        for image_name in ['hover_image', 'unclickable_image']:
            if not images.get(image_name):
                self.images[image_name] = images['image'].copy()

        self.image_state = 'image'
        self.render_image = self.images['image']

    def update(self: object,
               relative_game_speed: float) -> None:

        'Updates the button\'s render position and render size.\n\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'

        if self.scroll_opts:
            for i in range(2):
                # 0.5 because it will be rounded; it will be the wanted_scroll_pos when not scrolling
                if self.scroll_opts[i] and abs(self.wanted_scroll_pos[i] - self.render_pos[i]) >= 0.5:
                    self.render_pos[i] += (self.wanted_scroll_pos[i] - self.render_pos[i]) * (1 - 0.9**relative_game_speed)
                self.render_pos[i] = max(self.pos[i] - self.scroll_opts[i][1], min(
                    self.pos[i] + self.scroll_opts[i][0], self.render_pos[i]))
        # Resizing
        if self.rect.collidepoint(pg.mouse.get_pos()) and self.clickable:
            self.image_state = 'hover_image'

            # Smooth size change of button
            self.render_size = [self.render_size[0] + (self.size[0] * (1 + self.resize_opts[0]) - self.render_size[0]) * (1 - 0.9**relative_game_speed),
                                self.render_size[1] + (self.size[1] * (1 + self.resize_opts[0]) - self.render_size[1]) * (1 - 0.9**relative_game_speed)]
        elif self.clickable:
            self.image_state = 'image'

        else:
            self.image_state = 'unclickable_image'

        self.render_image = self.images[self.image_state]
        # Smooth size change of button
        # prevents unneccessary resizing (rounds anyway when rendered)
        # distributive property does not apply for booleans
        if (self.render_size[0] - self.size[0]) >= 1 and (not self.resize_opts[0] or not (self.rect.collidepoint(pg.mouse.get_pos()) and self.clickable)):
            self.render_size = [self.render_size[0] + (self.size[0] - self.render_size[0]) * (1 - 0.9**relative_game_speed),
                                # resize
                                self.render_size[1] + (self.size[1] - self.render_size[1]) * (1 - 0.9**relative_game_speed)]
        self.render_image = pg.transform.scale(
            self.render_image, (int(self.render_size[0]), int(self.render_size[1])))
        
        # I round here instead of when rendering because it will be inted (not an fRect) if it's not rounded here
        self.rect.update(round((self.size[0] - self.render_size[0]) / 2 + self.render_pos[0]),
                         round((self.size[1] - self.render_size[1]) / 2 + self.render_pos[1]),
                         self.render_size[0], self.render_size[1])
    def render(self: object,
               surf: pg.Surface) -> pg.Rect:

        'Renders the button onto the given surface.\n\n' \
        '   surf: pygame.Surface (required)\n' \
        '     the surface to render the button onto'

        return surf.blit(self.render_image, (self.rect.x, self.rect.y))

    def handle_events(self: object,
                      event: pg.event.Event) -> None:

        'The event handler of the Button class.\n\n' \
        '   event: pygame.event.Event (required)\n' \
        '     the event to handle'

        # I had to add the event.button check because scrolling sends this event with a different event.button
        if event.type == pg.MOUSEBUTTONDOWN and self.clickable and event.button == 1 and self.rect.collidepoint(event.pos):
            self.render_size = [self.size[0] * (1 + self.resize_opts[1]), self.size[1] * 1.2]
            exec(self.code)
        elif event.type == pg.MOUSEWHEEL and self.scroll_opts and (not self.scroll_opts[4] or self.scroll_opts[4].collidepoint(pg.mouse.get_pos())):
            # self.wanted_scroll_pos[0] = (round((self.render_pos[0] - self.pos[0]) / self.scroll_opts[2]) - int((event.x * self.scroll_opts[3]) / self.scroll_opts[2] - sign(
                # ceils the change if it's positive and floors it if it's negative (approx.)
                # event.x) * 0.99)) * self.scroll_opts[2] + self.pos[0]
            # self.wanted_scroll_pos[1] = (round((self.render_pos[1] - self.pos[1]) / self.scroll_opts[2]) + int((event.y * self.scroll_opts[3]) / self.scroll_opts[2] + sign(
                # ceils the change if it's positive and floors it if it's negative (approx.)
                # event.y) * 0.99)) * self.scroll_opts[2] + self.pos[1]
            # above commented is the old scroll
            self.wanted_scroll_pos[0] = (round((self.render_pos[0] - self.pos[0]) / self.scroll_opts[2]) - math.copysign(
                math.ceil(abs((event.x * self.scroll_opts[3]) / self.scroll_opts[2])), event.x)) * self.scroll_opts[2] + self.pos[0]

            self.wanted_scroll_pos[1] = (round((self.render_pos[1] - self.pos[1]) / self.scroll_opts[2]) + math.copysign(
                math.ceil(abs((event.y * self.scroll_opts[3]) / self.scroll_opts[2])), event.y)) * self.scroll_opts[2] + self.pos[1]


# This class is here so that the images are not an entire button; it has too many unused stuff
class MenuImage(Button):

    'The class for images in Menus. It exists so that there is no wasted functionality when adding images.'

    def __init__(self: object,
                 pos: list or tuple,
                 image: pg.Surface,
                 colorkey: tuple=0,
                 scroll: list or tuple=[]) -> None:

        'The initialization function of the MenuImage class.\n\n' \
        '   pos: list or tuple[int or float] (required)\n' \
        '     the starting position of the image in format (x, y)\n' \
        '     if x or y is a string, then it will be centered on that axis:\n' \
        '       it has two arguments: the screen width to center to, and the pixel ratio\n' \
        '       arguments are split by semicolons (;)\n' \
        '       E.g. "640;1"\n' \
        '   image: pygame.Surface (required)\n' \
        '     the image\n' \
        '   colorkey: tuple or color object (not required)\n' \
        '     the image\'s colorkey. is redundant if the image already has one\n' \
        '     can be used when the image is rendered' \
        '   scroll: list or tuple (not required)\n' \
        '     the mouse scroll settings of the image. it is a list containing 5 options\n' \
        '       0. the range of x-axis scrolling in format (max increase, max decrease)\n' \
        '       1. the range of y-axis scrolling in format (max increase, max decrease)\n' \
        '       2. the pixel ratio. the scroll will only land on multiples of this value.\n' \
        '          this can be used for pixel art.\n' \
        '       3. the scroll speed\n' \
        '       4. the scroll rectangle. if the mouse is in this rect, then scrolling is\n' \
        '          allowed. if it is 0, then scrolling will always be allowed.'

        self.scroll_opts = list(scroll)
        self.pos = []
        self.image = image
        size = image.get_size()
        for dex, position in enumerate(pos):
            if type(position) == str:
                # if it is a string, then it will center
                # arguments are split with semicolons
                # the first argument is the width of the screen
                # the second is the pixel ratio
                split_pos = tuple((int(item) for item in position.split(';')))
                self.pos.append(int((split_pos[0] - size[dex]) / 2 // split_pos[1] * split_pos[1]))
            else:
                self.pos.append(position)
        self.render_pos = list(self.pos)
        if colorkey:
            self.image.set_colorkey(colorkey)
        if scroll:
            self.wanted_scroll_pos = list(pos)
        self.clickable = 0

    def update(self: object,
               relative_game_speed: float) -> None:

        'Updates the image\'s render position if scrolling is enabled.\n\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'

        if self.scroll_opts:
            for i in range(2):
                # 0.5 because it will be rounded; it will be the wanted_scroll_pos when not scrolling
                if self.scroll_opts[i] and abs(self.wanted_scroll_pos[i] - self.render_pos[i]) >= 0.5:
                    self.render_pos[i] += (self.wanted_scroll_pos[i] - self.render_pos[i]) * (1 - 0.9**relative_game_speed)
                self.render_pos[i] = max(self.pos[i] - self.scroll_opts[i][1], min(
                    self.pos[i] + self.scroll_opts[i][0], self.render_pos[i]))

    def render(self: object,
               surf: pg.Surface) -> pg.Rect: # menu image can be used for platformer sprites, so i added offset

        'Renders the image onto the given surface.\n\n' \
        '   surf: pygame.Surface (required)\n' \
        '     the surface to render the button onto'

        return surf.blit(self.image, tuple(round(item) for item in self.render_pos))


class MenuAnimation(MenuImage):

    'The Animation class.'

    def __init__(self: object,
                 pos: list or tuple,
                 image_list: image_list,
                 frame_length: int or float,
                 scroll: list or tuple=[],
                 update_style: str='loop',
                 running: int or bool=0,
                 starting_frame: int or float=0) -> None:

        'The initialization function of the Animation class.\n\n' \
        '   pos: list or tuple[int or float] (required)\n' \
        '     the starting position of the animation in format (x, y)\n' \
        '     if x or y is a string, then it will be centered on that axis:\n' \
        '       it has two arguments: the screen width to center to, and the pixel ratio\n' \
        '       arguments are split by semicolons (;)\n' \
        '       E.g. "640;1"\n' \
        '   image_list: list[pygame.Surface] (required)\n' \
        '     the list of images for the animation\n' \
        '   frame_length: int or float (required)\n' \
        '     the amount of frames to show each image for\n' \
        '   scroll: list or tuple (not required)\n' \
        '     the mouse scroll settings of the animation. it is a list containing 5 options\n' \
        '       0. the range of x-axis scrolling in format (max increase, max decrease)\n' \
        '       1. the range of y-axis scrolling in format (max increase, max decrease)\n' \
        '       2. the pixel ratio. the scroll will only land on multiples of this value.\n' \
        '          this can be used for pixel art.\n' \
        '       3. the scroll speed\n' \
        '       4. the scroll rectangle. if the mouse is in this rect, then scrolling is allowed.\n' \
        '          if it is 0, then scrolling will always be allowed.\n' \
        '   update_style: str (not required)\n' \
        '     the style in which the button updates to. the three possible options are:\n' \
        '       "loop:" the animation loops after finishing\n' \
        '       "disappear:" the animation stops running after finishing\n' \
        '       "maxout:" the animation stays at the last frame after finishing\n' \
        '   running: int or bool (not required)\n' \
        '     if the animation should start as running or not' \
        '   starting_frame: int or float (not required)\n' \
        '     the starting frame of the animation.\n' \
        '     this is the game loop frame, not the numer of the image to start with'

        super().__init__(pos, image_list[-1], scroll)

        del self.image # removes an unneeded variable from superclass

        self.image_list = image_list
        self.frame_length = frame_length
        self.update_style = update_style

        self.full_cycle_length = self.frame_length * len(self.image_list)
        
        self.running = running
        self.game_loop_frame = starting_frame

        self.last_frame_rendered = int(self.game_loop_frame / self.frame_length)

    def update(self: object,
               relative_game_speed: float) -> None:

        'Updates the animation\'s render position if scrolling is enabled and frames.\n\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'

        super().update(relative_game_speed)
        if self.running:
            self.game_loop_frame += relative_game_speed
            if self.update_style == 'maxout':
                self.game_loop_frame = min(self.game_loop_frame, self.full_cycle_length - 1)
            elif self.update_style == 'loop':
                self.game_loop_frame %= self.full_cycle_length
            elif self.update_style == 'disappear' and self.game_loop_frame >= self.full_cycle_length:
                self.game_loop_frame = 0
                self.last_frame_rendered = 0
                self.running = 0
         
    def render(self: object,
               surf: pg.Surface,
               flip: list or tuple=(0, 0)) -> pg.Rect:

        'Renders the animation onto the given surface.\n\n' \
        '   surf: pygame.Surface (required)\n' \
        '     the surface to render the button onto'

        # this animation class can also be used for platformers, so i included "flip"
        if self.running:
            self.last_frame_rendered = int(self.game_loop_frame / self.frame_length)
            # ^ helps with playing sounds in cutscenes (modding doesn't work because of delta time)
            return surf.blit(pg.transform.flip(self.image_list[self.last_frame_rendered], flip[0], flip[1]), tuple(round(item) for item in self.render_pos))


class TextBox(Button):

    'The TextBox class.'

    def __init__(self: object,
                 game: object,
                 clickable: int or bool,
                 pos: list or tuple,
                 images: image_dict,
                 font_opts: list or tuple,
                 size: list or tuple=[],
                 code: str='',
                 scroll: list or tuple=[],
                 resize: list or tuple=[0, 0],
                 text_pos: list or tuple=[4, 4],
                 limit: int=100,
                 enter_code: str='',
                 validator: Callable=lambda x: 1) -> None:

        'The initialization function of the TextBox class.\n\n' \
        '   game: object (required)\n' \
        '     the game object of the text box. can be referred to in the text box\'s click code\n' \
        '   clickable: int or bool (required)\n' \
        '     a bool that tells whether the text box should be clickable.\n' \
        '     the clickability can be set through the clickable attribute\n' \
        '   pos: list or tuple[int or float] (required)\n' \
        '     the starting position of the text box in format (x, y)\n' \
        '     if x or y is a string, then it will be centered on that axis:\n' \
        '       it has two arguments: the screen width to center to, and the pixel ratio\n' \
        '       arguments are split by semicolons (;)\n' \
        '       E.g. "640;1"\n' \
        '   images: dict(str=pygame.Surface) (required)\n' \
        '     the images for the text box. accepts four images max, but "image" is required:\n' \
        '       "image:" the normal image for the text box\n' \
        '       "hover_image:" the image that displays when the text box is hovered over\n' \
        '       "unclickable_image:" the image that displays when the text box is unclickable\n' \
        '       "focused_image:" the image that displays when the text box is focused\n' \
        '   font_opts: list or tuple (required)\n' \
        '     a list containing the options for the font rendering of the text box. the items are:\n' \
        '       0. the font to be used when rendering\n' \
        '       1. whether or not to use antialiasing for rendering\n' \
        '       2. the color of the rendered text\n' \
        '       3. the background color of the rendered text\n' \
        '       4. the wrap length of the rendered text\n' \
        '   size: list or tuple[int or float] (not required)\n' \
        '     the size of the text box in format (width, height).\n' \
        '     this is the size used for calculations when resizing\n' \
        '   code: str or code object (not required)\n' \
        '     the code run when the text box is clicked. it is run with the exec() function\n' \
        '   scroll: list or tuple (not required)\n' \
        '     the mouse scroll settings of the text box. it is a list containing 5 options\n' \
        '       0. the range of x-axis scrolling in format (max increase, max decrease)\n' \
        '       1. the range of y-axis scrolling in format (max increase, max decrease)\n' \
        '       2. the pixel ratio. the scroll will only land on multiples of this value.\n' \
        '          this can be used for pixel art.\n' \
        '       3. the scroll speed\n' \
        '       4. the scroll rectangle. if the mouse is in this rect, then scrolling is allowed.\n' \
        '          if it is 0, then scrolling will always be allowed.\n' \
        '   resize: list or tuple[int or float] (not required)\n' \
        '     the resize settings for the text box in format (size increase when hovered, size increase when clicked)\n' \
        '   text_pos: list or tuple[int or float] (not required)\n' \
        '     the position inside the image to render the text\n' \
        '   limit: int (not required)\n' \
        '     the maximum number of characters to allow in the text box\n' \
        '   enter_code: str (not required)\n' \
        '     the code the run when the box is focused and the enter key is pressed\n' \
        '   validator: Callable (not required)\n' \
        '     the validator function to run on each character to see if the character is accepted'

        # For font_opts ^: 0 is font, 1 is antialiasing, 2 is color, 3 is bgcoolor, 4 is wraplength
        super().__init__(game, clickable, pos, images, size, code, scroll, resize)
        self._focused = 0
        self._text = ''
        self.render_text = '|' if self._focused else ''# includes the cursor
        self.cursor_pos = 0
        self.text_limit = limit
        self.text_pos = list(text_pos)
        self.font_opts = list(font_opts)
        self.enter_code = enter_code
        self.validator = validator

        if not images.get('focused_image'):
            self.images['focused_image'] = images['image'].copy()
    @property
    def focused(self: object) -> int:
        return self._focused

    @focused.setter
    def focused(self: object, value: int or bool) -> None:
        if type(value) == int or type(value) == bool:
            self._focused = value
            self._update_render_text()
            self._update_render_image()

    @property
    def text(self: object) -> str:
        return self._text
    
    @text.setter
    def text(self: object, value: str) -> None:
        if type(value) == str:
            self._text = value
            self._update_render_text()
            self._update_render_image()

    def _update_render_text(self: object) -> None:
        self.render_text = f'{self._text[:self.cursor_pos]}{'|' if self._focused else ''}{self._text[self.cursor_pos:]}'

    def _update_render_image(self: object) -> None:
        self.render_image = self.images[self.image_state].copy()
        self.render_image.blit(self.font_opts[0].render(
            self.render_text, self.font_opts[1], self.font_opts[2], bgcolor=self.font_opts[3], wraplength=self.font_opts[4]), self.text_pos)


    def update(self: object,
               relative_game_speed: float) -> None:

        'Updates the text box\'s render position if scrolling is enabled and render image.\n\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'

        super().update(relative_game_speed)
        if self._focused:
            self.image_state = 'focused_image'

        self._update_render_image()
        
    def handle_events(self: object,
                      event: pg.event.Event) -> None:

        'The event handler of the TextBox class.\n\n' \
        '   event: pygame.event.Event (required)\n' \
        '     the event to handle'

        if event.type == pg.KEYDOWN and self._focused:
            if event.key == pg.K_BACKSPACE:
                self._text = f'{self.text[:self.cursor_pos][:-1]}{self.text[self.cursor_pos:]}'
                self.cursor_pos = max(self.cursor_pos - 1, 0)
            elif event.key == pg.K_RETURN:
                exec(self.enter_code)
                self.cursor_pos = min(self.cursor_pos, len(self._text)) # here so that it takes one press of arrow key to move left, not two if text gets shorter
            elif event.key == pg.K_RIGHT:
                self.cursor_pos = min(self.cursor_pos + 1, len(self._text))
            elif event.key == pg.K_LEFT:
                self.cursor_pos = max(self.cursor_pos - 1, 0)
        elif event.type == pg.TEXTINPUT and len(self._text) < self.text_limit and self.validator(event.text) and self._focused:
            self._text = f'{self._text[:self.cursor_pos]}{event.text}{self._text[self.cursor_pos:]}'
            self.cursor_pos = min(self.cursor_pos + 1, len(self._text))

        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and self.clickable:
            self._focused = self.rect.collidepoint(event.pos)
            exec(self.code)
            self.cursor_pos = min(self.cursor_pos, len(self._text)) # here so that it takes one press of arrow key to move left, not two if text gets shorter

        elif self.scroll_opts and event.type == pg.MOUSEWHEEL and (not self.scroll_opts[4] or self.scroll_opts[4].collidepoint(pg.mouse.get_pos())):
            # self.wanted_scroll_pos[0] = (round((self.render_pos[0] - self.pos[0]) / self.scroll_opts[2]) - int((event.x * self.scroll_opts[3]) / self.scroll_opts[2] - sign(
                # ceils the change if it's positive and floors it if it's negative (approx.)
                # event.x) * 0.99)) * self.scroll_opts[2] + self.pos[0]
            # self.wanted_scroll_pos[1] = (round((self.render_pos[1] - self.pos[1]) / self.scroll_opts[2]) + int((event.y * self.scroll_opts[3]) / self.scroll_opts[2] + sign(
                # ceils the change if it's positive and floors it if it's negative (approx.)
                # event.y) * 0.99)) * self.scroll_opts[2] + self.pos[1]
            # above commented is the old scroll
            self.wanted_scroll_pos[0] = (round((self.render_pos[0] - self.pos[0]) / self.scroll_opts[2]) - math.copysign(
                math.ceil(abs((event.x * self.scroll_opts[3]) / self.scroll_opts[2])), event.x)) * self.scroll_opts[2] + self.pos[0]

            self.wanted_scroll_pos[1] = (round((self.render_pos[1] - self.pos[1]) / self.scroll_opts[2]) + math.copysign(
                math.ceil(abs((event.y * self.scroll_opts[3]) / self.scroll_opts[2])), event.y)) * self.scroll_opts[2] + self.pos[1]
        self._update_render_text()


class Menu(object):

    'The Menu class.'

    def __init__(self: object,
                 game: object,
                 background: list or tuple=(pg.Surface((0, 0)), None, (0, 0, 0)),
                 button_list: list or tuple=[]) -> None:

        'The initialization function of the Menu class.\n' \
        '   game: object (required)\n' \
        '     the game of the menu\n' \
        '   background: list or tuple (not required)\n' \
        '     the background of the menu it is list containing three items:\n' \
        '       0. the background surface\n' \
        '       1. the opacity of the background\n' \
        '       2. the color to fill the background with (put 0 for no fill)\n' \
        '   button_list: list or tuple (not required)\n' \
        '     the button list of the menu'

        self.game = game
        self.on = 0
        self.button_list = list(button_list) #creates a shallow copy; don't need
        self.background_surface = background[0].copy()
        if background[2]:
            self.background_surface.fill(background[2])
        self.background_surface.set_alpha(background[1])

    def update(self: object,
               relative_game_speed: float) -> None:

        'Updates the menu\'s buttons\' render positions if scrolling is enabled and render image.\n\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'

        if self.on:
            for button in self.button_list:
                button.update(relative_game_speed)

    def render(self: object,
               surf: pg.Surface) -> tuple:

        'Renders the menu onto the given surface.\n\n' \
        '   surf: pygame.Surface (required)\n' \
        '     the surface to render the button onto'

        if self.on:
            return (surf.blit(self.background_surface, (0, 0)), *(button.render(surf) for button in self.button_list))
        return (pg.Rect(0, 0, 0, 0),)


    def handle_events(self: object,
                      event: pg.event.Event) -> None:

        'The event handler of the Menu class.\n\n' \
        '   event: pygame.event.Event (required)\n' \
        '     the event to handle'

        if self.on:
            for button in self.button_list:
                button.handle_events(event)
                
    def run(self: object,
            surf: pg.Surface,
            game_speed: int,
            screen: pg.Surface=0, # if the surface is to be rendered again onto another surface
            toggle_keys: list or tuple[int]=[None]) -> None:

        'Runs the menu independently in its own game loop.\n\n' \
        '   surf: pygame.Surface (required)\n' \
        '     the surface to render the menu on\n' \
        '   game_speed: int (required)\n' \
        '     the game speed to run the menu with\n' \
        '   screen: pygame.Surface=0 (not required)\n' \
        '     the surfave to render the rendered surface on (if needed)\n' \
        '   toggle_keys: list or tuple[int] (not required)\n' \
        '     the list of keys that will toggle off the menu'

        self.on = 1
        start_time = time.time()
        pre_background = pg.Surface((0, 0))
        if screen:
            screen_size = screen.get_size()
        if self.background_surface.get_alpha() or self.background_surface.get_size() == (0, 0):
            pre_background = surf.copy() # for alpha backgrounds, it will still show old screen below the alpha layer
        while self.on:
            delta_time = time.time() - start_time
            start_time = time.time()
            for event in pg.event.get():
                self.handle_events(event)
                if event.type == pg.QUIT:
                    self.on = 0
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN and event.key in toggle_keys:
                    self.on = 0

            self.update(delta_time * game_speed)

            surf.blit(pre_background, (0, 0))
            self.render(surf)
            if screen:
                screen.blit(pg.transform.scale(surf, screen_size), (0, 0))
            pg.display.update()


class Cutscene(Menu):

    'The Cutscene class.'

    def __init__(self: object,
                 game: object,
                 dialogue: MenuAnimation, # animations in the menu
                 skip_dialogue_keys: list or tuple(int)=(pg.K_RETURN,), # a pygame key is an int
                 sound: mx.Sound=0, # sound to play for animation
                 background: list or tuple=(pg.Surface((0, 0)), None, (0, 0, 0)),
                 button_list: list or tuple=[],
                 ) -> None:

        'The initialization function of the Menu class.\n' \
        '   game: object (required)\n' \
        '     the game of the menu\n' \
        '   dialogue: Animation (required)\n' \
        '     the dialogue animation for the cutscene\n' \
        '   skip_dialogue_keys: list or tuple(int) (required)\n' \
        '     the list of keys that can be used to skip dialogue\n' \
        '   sound: mx.Sound (not required)\n' \
        '     the sound that plays when for each character in the dialogue\n' \
        '   background: list or tuple (not required)\n' \
        '     the background of the menu it is list containing three items:\n' \
        '       0. the background surface\n' \
        '       1. the opacity of the background\n' \
        '       2. the color to fill the background with (put 0 for no fill)\n' \
        '   button_list: list or tuple (not required)\n' \
        '     the button list of the menu'

        super().__init__(game, background, button_list)
        self.button_list.append(dialogue)
        self.color = background[2] # in case you stop; reset stuff
        dialogue.update_style = 'maxout' # needed for text
        self.sound = sound
        self.skip_dialogue_keys = skip_dialogue_keys

    def start_stop(self: object,
                   state: int or bool) -> None: # full start/end

        'Starts or stops the cutscene\n' \
        '   state: int or bool (required)\n' \
        '     the state to change the cutscene to (True for on, False for off)'

        self.on = state
        self.button_list[-1].running = state
        self.button_list[-1].game_loop_frame = 0
        if state and self.sound:
            self.sound.play()

    def update(self: object,
               relative_game_speed: float) -> None:

        'Updates the cutscenes\'s buttons\' render positions if scrolling is enabled and render image.\n\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'


        super().update(relative_game_speed)
        if self.on and self.sound and (self.button_list[-1].image_list[self.button_list[-1].last_frame_rendered] is not
                                       self.button_list[-1].image_list[int(self.button_list[-1].game_loop_frame / self.button_list[-1].frame_length)]):
            self.sound.play()
            # play sound every time it changes frames (like sans)
            # I use 'is not' because every new frame, it plays a sound
            # When creating dialogue animation with the 'create_dialogue_animation' function, punctuation repeats frames, as to pause when punctuation is read by the user
            # So -- since the repeated frames refer to the same object in memory (test using 'is not'), it won't play the sound multiple times; rather, only play it once

    def handle_events(self: object,
                      event: pg.event.Event) -> None:

        'The event handler of the Cutscene class.\n\n' \
        '   event: pygame.event.Event (required)\n' \
        '     the event to handle'

        if self.on:
            for button in self.button_list:
                button.handle_events(event)
            if event.type == pg.KEYDOWN and event.key in self.skip_dialogue_keys:
                self.button_list[-1].game_loop_frame = self.button_list[-1].full_cycle_length - 1

    def run(self: object,
            surf: pg.Surface,
            game_speed: int,
            screen: pg.Surface=0,
            toggle_keys: list or tuple[int]=[None],
            auto_time: int=-1) -> None:

        'Runs the cutscene independently in its own game loop.\n\n' \
        '   surf: pg.Surface (required)\n' \
        '     the surface to render the cutscene on\n' \
        '   game_speed: int (required)\n' \
        '     the game speed to run the cutscene with\n' \
        '   screen: pg.Surface=0 (not required)\n' \
        '     the surface to render the rendered surface on (if needed)\n' \
        '   toggle_keys: list or tuple[int] (not required)\n' \
        '     the list of keys that will toggle off the menu\n' \
        '   auto_time: int (not required)\n' \
        '     the time for that cutscene to automatically switch off (leave as -1 for unlimited)'

        self.start_stop(1)
        start_time = time.time()
        pre_background = pg.Surface((0, 0))
        # pre_background.fill((0, 0, 0))
        if screen:
            screen_size = screen.get_size()
        auto_time_buffer = 0
        if self.background_surface.get_alpha() or self.background_surface.get_size() == (0, 0):
            pre_background = surf.copy() # for alpha backgrounds, it will still show old screen below the alpha layer
        while self.on:
            delta_time = time.time() - start_time
            start_time = time.time()
            for event in pg.event.get():
                self.handle_events(event)
                if event.type == pg.QUIT:
                    self.start_stop(0)
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN and event.key in toggle_keys:
                    self.start_stop(0)

            self.update(delta_time * game_speed)

            if auto_time != -1 and (self.button_list[-1].game_loop_frame >=
                                    self.button_list[-1].full_cycle_length - 1):
                auto_time_buffer += delta_time * game_speed
                if auto_time_buffer >= auto_time:
                    self.start_stop(0)

            surf.blit(pre_background, (0, 0))
            self.render(surf)
            if screen:
                screen.blit(pg.transform.scale(surf, screen_size), (0, 0))
            pg.display.update()

class CutsceneSlideshow(object):

    'The CutsceneSlideshow class.'

    def __init__(self: object,
                 game: object,
                 cutscene_list: list or tuple(Cutscene), 
                 control_keys: list or tuple(int)=(pg.K_RIGHT, pg.K_LEFT, pg.K_ESCAPE),
                 transition_style: str='fade',
                 transition_frames: int=510, # only applicable for fade tranisitions
                 finish_code: str='',
                 auto_time: int=-1) -> None:

        'The initialization function of the CutsceneSlideshow class.\n' \
        '   game: object (required)\n' \
        '     the game of the slideshow\n' \
        '   cutscene_list: list or tuple(Cutscene) (required)\n' \
        '     the list of cutscenes for the slideshow\n' \
        '   control_keys: list or tuple(int) (not required)\n' \
        '     the list of keys that can be used to navigate (first key goes to next slide,\n' \
        '     next key goes to previous slide, final key exits the slideshow)'
        '   transition_style: str (not required)\n' \
        '     the style of transition between slides (\'fade\' for fade and \'jump\' for jumpcut)\n' \
        '   transition_frames: int (not required)\n' \
        '     the amount of frames a fade transition lasts (accounts for delta time)\n' \
        '   finish_code: str (not required)\n' \
        '     the code that runs when the slideshow is finished\n' \
        '   auto_time: int (not required)\n' \
        '     the amount of time in frames for the slideshow to move to the next slide\n' \
        '     (-1 for no auto switching)'

        # if auto_time == -1, then auto is disabled

        # for control_keys  ^: first is the next_key, second is the previous_key, third is the exit key
        # for transition_style ^ 'fade' is for a fade transition and 'jump' is for a jumpcut
        self.game = game
        self.on = 0
        self.finish_code = finish_code
        self.current_slide = 0
        if transition_style == 'fade':
            self.transition_state = 0 # if 1, then alpha is increasing; if -1, then alpha is decreasing
            self.transition_frames = transition_frames # number of frames (relative to game speed) for a fade transition (speed of transition)
            self.alpha = 0

        self.wanted_slide = 0 # for the changing slide thing 

        self.transition_style = transition_style
        self.cutscene_list = cutscene_list
        self.control_keys = control_keys
        self.auto_time = auto_time # number of frames to wait before automatically switching slides
        self.auto_time_buffer = 0 # current number of frames passed

    def start_stop(self: object,
                   state: int or bool) -> None: # full start/end

        'Starts or stops the slideshow\n' \
        '   state: int or bool (required)\n' \
        '     the state to change the cutscene to (True for on, False for off)'

        self.on = state
        if state:
            if self.transition_style == 'fade':
                self.transition_state = 0 # if 1, then alpha is increasing; if -1, then alpha is decreasing
                self.alpha = 0
            self.current_slide = 0

        self.cutscene_list[min(self.current_slide, len(self.cutscene_list) - 1)].start_stop(state)

    def update_auto_time_buffer(self: object,
                                relative_game_speed: float) -> None:

        'Updates the auto time buffer (the time counter for automatic closing)\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'

        # this is a private method, but this version of pygwig does not include encapsulation
        self.auto_time_buffer += relative_game_speed
        if self.auto_time_buffer >= self.auto_time:
            self.auto_time_buffer = 0 # switching to next frame
            pg.event.post(pg.event.Event(pg.KEYDOWN, {'key': self.control_keys[0]}))

    def update(self: object,
               relative_game_speed: float) -> None:

        'Updates the slideshow\'s cutscene\'s button positions if scrolling is enabled and render image.\n' \
        '   relative_game_speed: float (required)\n' \
        '     the delta time to update the values to'

        if self.on:
            self.cutscene_list[self.current_slide].update(relative_game_speed)
            if self.transition_style == 'fade' and self.transition_state:
                self.alpha = min(max(self.alpha + self.transition_state * relative_game_speed * 255 / self.transition_frames * 2, 0), 255)
                if self.alpha == 255:
                    self.transition_state = -1
                    self.cutscene_list[self.current_slide].start_stop(0)
                    if self.wanted_slide < len(self.cutscene_list):
                        self.cutscene_list[self.wanted_slide].start_stop(1)
                        self.current_slide = self.wanted_slide
                    else:
                        exec(self.finish_code)

                elif not self.alpha:
                    self.transition_state = 0
                    if self.wanted_slide == len(self.cutscene_list):
                        self.start_stop(0) # not executing finish code because it was already ran
                    if self.auto_time != -1:
                        self.update_auto_time_buffer(relative_game_speed)
            elif self.auto_time != -1 and (self.cutscene_list[self.current_slide].button_list[-1].game_loop_frame >=
                                           self.cutscene_list[self.current_slide].button_list[-1].full_cycle_length - 1):
                self.update_auto_time_buffer(relative_game_speed)

    def render(self: object,
               surf: pg.Surface) -> tuple:

        'Renders the slideshow onto the given surface.\n\n' \
        '   surf: pygame.Surface (required)\n' \
        '     the surface to render the button onto'

        if self.on:
            if self.transition_style == 'fade':
                transition_surface = pg.Surface(surf.get_size())
                transition_surface.set_alpha(int(self.alpha))
            return (*self.cutscene_list[self.current_slide].render(surf), surf.blit(transition_surface, (0, 0)) if self.transition_style == 'fade' and self.transition_state else None)
        return (pg.Rect(0, 0, 0, 0),)

    def handle_events(self: object,
                      event: pg.event.Event) -> None:
        'The event handler of the CutsceneSlideshow class.\n\n' \
        '   event: pygame.event.Event (required)\n' \
        '     the event to handle'

        if self.on:
            self.cutscene_list[self.current_slide].handle_events(event)
            if event.type == pg.KEYDOWN:
                change = (event.key == self.control_keys[0]) - (event.key == self.control_keys[1])
                if event.key == self.control_keys[2]:
                    if self.transition_style == 'fade':
                        if self.wanted_slide < len(self.cutscene_list):
                            self.wanted_slide = len(self.cutscene_list)
                            self.transition_state = 1
                    else:
                        self.start_stop(0)
                        exec(self.finish_code)
                elif change and self.wanted_slide < len(self.cutscene_list):
                    self.wanted_slide = self.current_slide + change
                    if self.wanted_slide >= 0:
                        if self.transition_style == 'fade':
                            self.transition_state = 1
                        else:
                            self.cutscene_list[self.current_slide].start_stop(0)
                            if self.wanted_slide == len(self.cutscene_list):
                                self.start_stop(0)
                                exec(self.finish_code)
                            else:
                                self.current_slide = self.wanted_slide
                                self.cutscene_list[self.current_slide].start_stop(1)

    def run(self: object,
            surf: pg.Surface,
            game_speed: int,
            screen: pg.Surface=0) -> None:

        'Runs the slideshow independently in its own game loop.\n\n' \
        '   surf: pygame.Surface (required)\n' \
        '     the surface to render the slideshow on\n' \
        '   game_speed: int (required)\n' \
        '     the game speed to run the cutscene with\n' \
        '   screen: pygame.Surface=0 (not required)\n' \
        '     the surface to render the rendered surface on (if needed)\n' \


        # the screen argument is so that the cutscene can be rendered onto a surface and the surface will be rendered onto the screen

        self.start_stop(1)
        start_time = time.time()
        pre_background = surf.copy() # for alpha backgrounds, it will still show old screen below the alpha layer
        if screen:
            screen_size = screen.get_size()
        while self.on:
            delta_time = time.time() - start_time
            start_time = time.time()
            for event in pg.event.get():
                self.handle_events(event)
                if event.type == pg.QUIT:
                    self.start_stop(0)
                    pg.quit()
                    sys.exit()
            self.update(delta_time * game_speed)
            if self.transition_style == 'fade' and self.wanted_slide == len(self.cutscene_list) and self.transition_state == -1:
                break
                # so it will be rendered on the screen after it has ran (final fade transition)
                # this is why one should also put the render statement into the mainloop
            surf.blit(pre_background, (0, 0))
            self.render(surf)
            if screen:
                screen.blit(pg.transform.scale(surf, screen_size), (0, 0))
            pg.display.update()

