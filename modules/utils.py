from collections.abc import Iterable
import math
import pygame as pg

BASE_IMG_PATH = 'data/images/'

type image_list = list[pg.Surface]

ROMAN_INDICATOR = (
            (1000, 'M'),
            (900, 'CM'),
            (500, 'D'),
            (400, 'CD'),
            (100, 'C'), 
            (90, 'XC'),
            (50, 'L'),
            (40, 'XL'),
            (10, 'X'),
            (9, 'IX'),
            (5, 'V'),
            (4, 'IV'),
            (1, 'I'),
            )

# credit to Aristide on StackOverflow for this clean solution
# under CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/
# algorithm is the same but I changed the variable names
def arabic_to_roman(number: int) -> str: 

    """
    Converts Arabic numerals into their Roman numeral counterpart.
       number: int (required)
         the Arabic number to convert to Roman numerals
    """

    result = ''
    if number:
        for arabic, roman in ROMAN_INDICATOR:
            (factor, number) = divmod(number, arabic)
            result += factor * roman
            if not number:
                break
    else:
        result = '0'
    return result

# Credit to Ashwini Chaudhary StackOverflow for this function
# Under CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0/
# I added a return_type paremeter
def element_wise_addition(*args: Iterable,
                          return_type: type=int) -> list:
    
    """
    Adds lists together element-wise.
       *args: Iterable[int or float] (required)
         the lists to add (element-wise)
       return_type: type (not required)
         the type of number to return in the list
    """
    
    return [return_type(sum(item)) for item in zip(*args)]

def load_img(path: str,
             size: list or tuple) -> pg.Surface:
    """
    Loads images in one function.
       path: str (required)
         the file path of the image
       size: list or tuple (required)
         the size of the returned image
    """

    try:
        img = pg.transform.scale(pg.image.load(f'{BASE_IMG_PATH}{path}'), size).convert()
        img.set_colorkey((0, 0, 0))
    except:
        img = pg.transform.scale(pg.image.load(f'{BASE_IMG_PATH}forgot_to_install_source.png'), size).convert()
    return img


def load_img_series(path: str,
                    size: list or tuple,
                    number_of_images: int,
                    prefix: str='') -> image_list:
    
    """
    Loads multiple images.
       path: str (required)
         the folder path of the images
       size: list or tuple (required)
         the size of the returned images
       number_of_images: int (required)
         the number of images in the folder
       prefix: str (not required)
         the prefix for the images (eg. space; the first image will be space0)
    """

    images = []
    for i in range(number_of_images):
        images.append(load_img(f'{path}/{prefix}{i}.png', size))
    return images


def load_img_from_spritesheet(spritesheet: pg.Surface,
                              rect: pg.Rect) -> pg.Surface:

    """
    Loads a single image from a spritesheet.
       spritesheet pygame.Surface (required)
         the surface of the spritesheet
       rect: pygame.Rect (required)
         the rect of the portion of the image
    """

    surface = pg.Surface(rect.size)
    surface.set_colorkey((0, 0, 0))
    surface.blit(spritesheet, (0, 0), area=rect)

    return surface


def load_spritesheet(spritesheet: pg.Surface,
                     size: list or tuple, # size of one sprite
                     number_of_imgs: int,
                     row_length: int=0, # number of images in one row
                     starting_pos: list or tuple=(0, 0)) -> image_list:

    """
    Loads multiple images from a spritesheet.
       spritesheet pygame.Surface (required)
         the surface of the spritesheet
       size: list or tuple (required)
         the size of each sprite
       number_of_imgs: int (not required)
         the number of sprites to load
       row_length: int (not required)
         the length of each row of the spritesheet
       starting_pos: list or tuple (not required)
         the starting position for the image loading
    """

    if row_length == 0:
        row_length = number_of_imgs
    image_list = []
    for i in range(number_of_imgs):
        image_list.append(load_img_from_spritesheet(
            spritesheet, pg.Rect(i % row_length * size[0] + starting_pos[0], int(i / row_length) * size[1] + starting_pos[1], size[0], size[1])))
    return image_list


def scientific_notation(num: int or float,
                        condition: int or bool=1,
                        max_decimals: int=3) -> str:

    """
    Converts a number to scientific notation.
       num: int or float (required)
         the number to convert to scientific notation
       condition: int or bool (not required)
         True or False; True for yes convert, false for no convert
       max_decimals: int (not required)
         the max amount of decimals in the returned number
    """

    if condition and num:
        power_of_ten = math.floor(math.log10(abs(num))) # I use abs so that it will work with negative numbers, rest is takeen care of
        return f'{round(num / 10**power_of_ten, max_decimals)} x 10^{power_of_ten}'
    return str(num)


def center_word_on_image(image: pg.Surface,
                         text_ratio: int or float=1,
                         text_sequence: image_list=[pg.Surface((0, 0))],
                         pos: list or tuple=('center', 'center')) -> pg.Surface:
    """
    Centers word(s) on an image.
       image: pygame.Surface (required)
         the image to center the word(s) on
       text_ratio: int or float (not required)
         the ratio of screen size to text size
       text_sequence: image_list (not required)
         the list of rendered texts
       pos: list or tuple (not required)
         a tuple containing positions for the texts. for each
         position, you can put "center" and it will center the
         words on that axis. if it is not "center", you can specify
         the position
    """

    # pos is for custom positions
    # Text_ratio just tells the ratio of the size of the image and the size of the text
    final_image = image.copy()
    height_of_text_block_so_far = 0
    height_of_full_text_block = sum(
        [text.get_height() * text_ratio for text in text_sequence])
    text_sequence = text_sequence.copy()
    render_pos = list(pos)

    # the ceiling dividing and multiplying makes it so the coordinates are multiples of the text ratio (keeps pixel ratio)
    # The - 1 in the y shifts it up to account for font extra height
    for text in text_sequence:
        text = pg.transform.scale(
            text, (text.get_width() * text_ratio, text.get_height() * text_ratio))
        render_pos = list(pos)
        if pos[0] == 'center':
            render_pos[0] = -(((final_image.get_width() -
                              text.get_width()) / text_ratio) // -2) * text_ratio
        if pos[1] == 'center':
            render_pos[1] = (((final_image.get_height(
            ) - height_of_full_text_block) / text_ratio) // 2 - 1) * text_ratio
        render_pos[1] += height_of_text_block_so_far
        final_image.blit(text, render_pos)
        height_of_text_block_so_far += text.get_height()
    return final_image


# Will not support (0, 0, 0) or alpha pixels (alpha pixels are slow, and black is the colorkey)
def render_rect(color: tuple or pg.Color,
                rect: pg.Rect,
                width: int or float=0,
                outline_color: tuple or pg.Color=0,
                outline_width: tuple or pg.Color=0) -> pg.Surface:
    
    """
    Renders a pygame rectangle.
       color: tuple or pg.Color (required)
         the color to render the rectangle
       rect: pygame.Rect (required)
         the rectangle to render
       width: int or float (not required)
         the width of the rectangle's border (if it is rendered)
       outline_color: tuple or pygame.Color (not required)
         the color of the custom outline (doesn't do anything if width is passed)
       outline_width: the width of the outline (not required)
         the width of the custom outline
    """

    surface = pg.Surface(rect.size).convert()
    surface.set_colorkey((0, 0, 0))
    pg.draw.rect(surface, color, rect, width)
    if outline_color:
        pg.draw.rect(surface, outline_color, rect, outline_width)
    return surface


def math_eval(string: str,
              exception_number: int or float,
              return_type: type=float) -> object:
    
    """
    Evaluates string expressions safely.
       string: str (required)
         the string expression
       exception_number: int or float (required)
         the number that will be returned if the expression is not valid
       return_type: type (not required)
         the type the return value will be
    """

    try:
        return return_type(eval(''.join(list((filter(lambda x: x in '0123456789^*/%+-().', string.replace('^', '**').replace('x', '*')))))))
        # I add the float() because then it will raise an exception if above 4300 digits. else, it would return it and the exception would happen outside of the function
    except:
        return exception_number


def last_index_greater_than_zero(number_list: list or tuple,
                                 exception_number: int=0) -> int:

    """
    Returns the index of the last number greater than zero.
       exception_number: int (not required)
         the number to return if all numbers are zero
    """

    for i in range(len(number_list) - 1, -1, -1):
        if number_list[i]:
            return i
    return exception_number


def create_dialogue_animation(text: str,
                              font_opts: list or tuple) -> list:

    """
    Creates an animation where characters are added one by one.
       text: str (required)
         the text to use in the animation
       font_opts: list or tuple (required)
         the options for font rendering:
           0: font
           1: antialiasing
           2: color
           3: bgcolor
           4: wraplength
    """

    image_list = []
    for i in range(len(text)):
        rendered_text = font_opts[0].render(text[:i + 1], font_opts[1], font_opts[2], bgcolor=font_opts[3], wraplength=font_opts[4])
        rendered_text.set_colorkey((0, 0, 0))
        for j in range((text[i] in ',.;:!') * 2 + 1):
            # adding extra images so that it pauses on punctuation. 
            # Since the repeated frames refer to the same memory address, a sound will not play multiple times when showing dialogue; only once
            image_list.append(rendered_text)
    return image_list


def text_on_big_button(text: str,
                       image_list: list or tuple, # the images you want the return dict to have
                       font: pg.font.Font) -> pg.Surface:
    
    """
    Renders text on the big button using the big button texture.
       text: str (required)
         the text to render on the button. it is preferred to be
         less than 4 characters
       image_list: list or tuple (required)
         the images that will be returned (any number of "image", "hover_image", "unclickable_image")
       font: pg.font.Font (required)
         the font to be used on the buttons (pixel ratio is 4)
    """

    return_dict = {
            'image': center_word_on_image(load_img('shop/button/button/big_button/big_shop_button.png', (128, 64)), 4, [font.render(text, 0, (255, 255, 255), bgcolor=(155, 173, 183))]),
            'hover_image': center_word_on_image(load_img('shop/button/button/big_button/big_shop_button_hover.png', (128, 64)), 4, [font.render(text, 0, (255, 255, 255), bgcolor=(174, 189, 197))]),
            'unclickable_image': center_word_on_image(load_img('shop/button/button/big_button/big_shop_button_unclickable.png', (128, 64)), 4, [font.render(text, 0, (180, 180, 180), bgcolor=(110, 123, 130))])
            }
    for image_name in return_dict.copy():
        if image_name not in image_list:
            return_dict.pop(image_name)
    return return_dict


def render_menu_top_bar(text: str,
                        font: pg.font.Font) -> pg.Surface:
    
    """
    Renders a top bar for a menu.
       text: str (required)
         the text to use in the top bar
       font: pygame.font.Font (required)
         the font to use for the top bar (pixel ratio is 4)
    """

    final_surface = pg.Surface((648, 64)) # only see one part of outline
    final_surface.blit(center_word_on_image(render_rect((3, 3, 3), pg.Rect(0, 0, 648, 68), outline_color=(255, 255, 255), outline_width=4), 4, [font.render(text, 0, (255, 255, 255), bgcolor=(3, 3, 3))]), (-4, -4))
    return final_surface

