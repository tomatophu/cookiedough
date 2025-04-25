"""The main file of Cookiedough. This file should be run."""

import os
import math
import time
import random
import json
import pygame as pg
from pygame import mixer as mx
from modules.pygwig import (
        Button,
        TextBox,
        MenuImage,
        MenuAnimation as Animation,
        Menu,
        Cutscene,
        CutsceneSlideshow as Slideshow,
        )

from modules.utils import (
        load_img,
        load_img_series,
        scientific_notation,
        center_word_on_image,
        render_rect,
        text_on_big_button,
        render_menu_top_bar,
        last_index_greater_than_zero,
        create_dialogue_animation,
        arabic_to_roman,
        )


# Notes
# For hover button images, overlay a layer of white that is at 50 opacity in aseprite
# For unclickable button images, the black added is at 75 opacity in aseprite
# For dithering, use the 4x4 Bayer Matrix
# I use predrawn images instead of creating a function that overlays the color because the function would interfere with colorkeys

class Game(object):

    """The main game class of Cookiedough."""

    def __init__(self: object) -> None:

        """Defines all variables and runs all needed functions to initialize Cookiedough."""

        # Initializations
        pg.init()
        pg.event.set_blocked((pg.MOUSEMOTION,
                              pg.MOUSEBUTTONUP,

                              pg.WINDOWMOVED,
                              pg.WINDOWENTER,
                              pg.WINDOWLEAVE,
                              pg.WINDOWFOCUSLOST,
                              pg.WINDOWFOCUSGAINED,
        
                              pg.VIDEOEXPOSE,
                              pg.VIDEORESIZE,
                              pg.ACTIVEEVENT,
                              ))
        # Window
        self.screen_size = (640, 360)
        self.surface_ratio = (1/4, 1/4)
        self.surface_size = (int(self.screen_size[0] * self.surface_ratio[0]),
                             int(self.screen_size[1] * self.surface_ratio[1]))
        self.screen = pg.display.set_mode(self.screen_size, flags=pg.RESIZABLE | pg.SCALED, vsync=1)
        self.surface = pg.Surface(self.surface_size).convert()
        self.game_speed = 60
        self.second_timer = pg.event.custom_type()
        pg.time.set_timer(self.second_timer, 1000)
        pg.display.set_icon(load_img('cookie/cookie.png', (128, 128)))
        pg.display.set_caption('Cookiedough')

        # Save data
        self.save_data = {'score': 0,
                          'total_baked_cookies': 0,
                          'cookies_per_second': 0,
                          'cookies_per_click': 1,
                          'cookies_per_day_counter': 0, # counter for each second for cookies per day * the amount of trees
                          'last_logout': time.time(),
                          'cookie_tree_values': [0] * 11, # Valuse for amount of trees with specified cookies
                          'auto_harvesters': 0,
                          'last_cutscene': -1, # last cutscene showed; -1 if none have been showed
                          'constant_cookies_level': 0,
                          'special_cookies_level': 0,
                          'seconds_until_next_special_cookie': 0,
                          }
        try:
            with open('data/save/save.json', 'r', encoding='UTF-8') as save_file:
                self.save_data = json.load(save_file)
        except FileNotFoundError:
            self.save_save_data_to_file()

        # Config data
        self.config_data = {
            # The buy amounts for each item (for buying in bulk)
            'item_shop_buy_numbers': [1, 1, 1, 1],
        }
        try:
            with open('data/save/config.json', 'r', encoding='UTF-8') as config_file:
                self.config_data = json.load(config_file)
        except FileNotFoundError:
            self.save_config_data_to_file()

        # Fonts
        self.font = pg.font.Font('data/font/Pixbob_Bold.ttf', 10)
        self.font_center = pg.font.Font('data/font/Pixbob_Bold.ttf', 10)
        self.font_center.align = pg.FONT_CENTER

        self.small_font = pg.font.Font('data/font/Pixbob.ttf', 10)
        small_font_scaled = pg.font.Font('data/font/Pixbob.ttf', 40)
        small_font_center = pg.font.Font('data/font/Pixbob.ttf', 10)
        small_font_center.align = pg.FONT_CENTER

        # Sounds
        self.sfx = {
                'dialogue': mx.Sound('data/sounds/dialogue.wav')
                }
        self.music = {
                }
        # Images
        self.cookie_imgs = {'image': load_img('cookie/cookie.png', (128, 128)),
                            'hover_image': load_img('cookie/cookie_hover.png', (128, 128))}

        self.background = load_img('background.png', self.surface.get_size())
        cookies_render = self.font.render('Cookies', 0, (255, 255, 255), bgcolor=(0, 0, 0))
        cookies_render.set_colorkey((0, 0, 0))
        self.background.blit(cookies_render, (24 - ((self.cookie_imgs['image'].get_width(
        ) * self.surface_ratio[0] - cookies_render.get_width()) // -2), 9))
        self.red_dot = load_img('earth_cam/red_dot.png', (4, 4))
        self.earth_imgs = load_img_series('earth_cam', (76, 86), 9, 'stage_')

        self.shop_exit_button_imgs = {'image': load_img('shop/button/exit/exit.png', (44, 44)),
                                      'hover_image': load_img('shop/button/exit/exit_hover.png', (44, 44))}
        self.arrow_imgs = ({'image': load_img('shop/button/arrow.png', (32, 12))},
                           {'image': pg.transform.flip(load_img('shop/button/arrow.png', (32, 12)), 0, 1)})
        self.switch_imgs = ({'image': load_img('shop/button/switch/switch.png', (52, 44)),
                             'hover_image': load_img('shop/button/switch/switch_hover.png', (52, 44)),
                             'unclickable_image': load_img('shop/button/switch/switch_unclickable.png', (52, 44))},
                            {'image': pg.transform.flip(load_img('shop/button/switch/switch.png', (52, 44)), 1, 0),
                             'hover_image': pg.transform.flip(load_img('shop/button/switch/switch_hover.png', (52, 44)), 1, 0),
                             'unclickable_image': pg.transform.flip(load_img('shop/button/switch/switch_unclickable.png', (52, 44)), 1, 0)})

        self.item_imgs = (load_img('shop/button/item_shop/auto_harvester.png', (128, 128)),
                          load_img('shop/button/item_shop/tree.png', (128, 128)),
                          load_img('shop/button/item_shop/oven.png', (128, 128)),
                          load_img('shop/button/item_shop/perpetual_cog.png', (128, 128)))
        self.upgrade_imgs = (load_img('shop/button/upgrade_shop/special_cookie.png', (128, 128)),
                             load_img('shop/button/upgrade_shop/constant_cookies.png', (128, 128)))

        self.farm_tree_imgs = {'image': load_img('shop/button/item_shop/tree.png', (128, 128)),
                               'hover_image': load_img('farm/button/tree/tree_hover.png', (128, 128)),
                               'unclickable_image': load_img('farm/button/tree/tree_unclickable.png', (128, 128))}

        self.special_cookie_imgs = ({'image': load_img('cookie/special/stone/stone_cookie.png', (128, 128)),
                                     'hover_image': load_img('cookie/special/stone/stone_cookie_hover.png', (128, 128))},
                                    {'image': load_img('cookie/special/bronze/bronze_cookie.png', (128, 128)),
                                     'hover_image': load_img('cookie/special/bronze/bronze_cookie_hover.png', (128, 128))},
                                    {'image': load_img('cookie/special/silver/silver_cookie.png', (128, 128)),
                                     'hover_image': load_img('cookie/special/silver/silver_cookie_hover.png', (128, 128))},
                                    {'image': load_img('cookie/special/gold/gold_cookie.png', (128, 128)),
                                     'hover_image': load_img('cookie/special/gold/gold_cookie_hover.png', (128, 128))},
                                    {'image': load_img('cookie/special/emerald/emerald_cookie.png', (128, 128)),
                                     'hover_image': load_img('cookie/special/emerald/emerald_cookie_hover.png', (128, 128))})

        self.special_cookie_eating_animation_imgs = ([load_img('cookie/special/stone/bite/stone_bite_1.png', (128, 128)),
                                                      load_img('cookie/special/stone/bite/stone_bite_2.png', (128, 128)),
                                                      load_img('cookie/special/stone/bite/stone_bite_3.png', (128, 128)),
                                                      load_img('cookie/special/stone/bite/stone_bite_4.png', (128, 128))],
                                                     [load_img('cookie/special/bronze/bite/bronze_bite_1.png', (128, 128)),
                                                      load_img('cookie/special/bronze/bite/bronze_bite_2.png', (128, 128)),
                                                      load_img('cookie/special/bronze/bite/bronze_bite_3.png', (128, 128)),
                                                      load_img('cookie/special/bronze/bite/bronze_bite_4.png', (128, 128))],
                                                     [load_img('cookie/special/silver/bite/silver_bite_1.png', (128, 128)),
                                                      load_img('cookie/special/silver/bite/silver_bite_2.png', (128, 128)),
                                                      load_img('cookie/special/silver/bite/silver_bite_3.png', (128, 128)),
                                                      load_img('cookie/special/silver/bite/silver_bite_4.png', (128, 128))],
                                                     [load_img('cookie/special/gold/bite/gold_bite_1.png', (128, 128)),
                                                      load_img('cookie/special/gold/bite/gold_bite_2.png', (128, 128)),
                                                      load_img('cookie/special/gold/bite/gold_bite_3.png', (128, 128)),
                                                      load_img('cookie/special/gold/bite/gold_bite_4.png', (128, 128))],
                                                     [load_img('cookie/special/emerald/bite/emerald_bite_1.png', (128, 128)),
                                                      load_img('cookie/special/emerald/bite/emerald_bite_2.png', (128, 128)),
                                                      load_img('cookie/special/emerald/bite/emerald_bite_3.png', (128, 128)),
                                                      load_img('cookie/special/emerald/bite/emerald_bite_4.png', (128, 128))])

        self.constant_shop_gui_img = load_img('shop/constant_gui.png', (self.screen_size[0], self.screen_size[1] - 64))
        self.main_menu_background = load_img('main_menu/main_menu_background.png', self.screen_size)
        # images with big button
        self.buy_button_imgs = text_on_big_button('Buy', ['image', 'hover_image', 'unclickable_image'], self.font)
        self.buy_button_number_imgs = text_on_big_button('Bulk', ['image', 'hover_image'], self.font) # buy_button_number is just the amount to buy (set in the bulk menu)
        self.save_button_imgs = text_on_big_button('Save', ['image', 'hover_image'], self.font)
        self.clear_button_imgs = text_on_big_button('Clear', ['image', 'hover_image'], self.font)
        self.shop_open_button_imgs = text_on_big_button('Shop', ['image', 'hover_image'], self.font)
        self.play_button_imgs = text_on_big_button('Play', ['image', 'hover_image'], self.font)
        self.farm_open_button_imgs = text_on_big_button('Farm', ['image', 'hover_image'], self.font)
        
        self.settings_button_imgs = {'image': load_img('main_menu/button/settings/settings_button.png', (128, 64)),
                                     'hover_image': load_img('main_menu/button/settings/settings_button_hover.png', (128, 64))}
        
        # I don't use """ for multiline strings, as I get indentation errors
        shop_exit_button_code = 'self.game.shop_list[self.game.current_shop_menu[0]].on = 0\n' \
                                'self.game.shop_button_menu_list[self.game.current_shop_menu[0]][self.game.current_shop_menu[1]].on = 0'
        # I use the multiline strings like this when the line is super long
        right_arrow_code = 'self.game.shop_list[self.game.current_shop_menu[0]].on = 0\n' \
                           'self.game.shop_list[self.game.current_shop_menu[0] + 1].on = 1\n' \
                           'pg.event.post(pg.event.Event(pg.MOUSEWHEEL, {"x": 0, "y": 0}))\n' \
                           'self.game.set_button_clickable()'
        left_arrow_code = 'self.game.shop_list[self.game.current_shop_menu[0]].on = 0\n' \
                          'self.game.shop_list[self.game.current_shop_menu[0] - 1].on = 1\n' \
                          'pg.event.post(pg.event.Event(pg.MOUSEWHEEL, {"x": 0, "y": 0}))\n' \
                          'self.game.set_button_clickable()'


        self.shop_list = [Menu(self, button_list=[
            # Shop items
            MenuImage((480, -172), self.item_imgs[0], scroll=[(0, 0), (320, 160), 160, 40, pg.Rect(448, 0, 192, 360)]),
            MenuImage((480, -12), self.item_imgs[1], scroll=[(0, 0), (320, 160), 160, 40, pg.Rect(448, 0, 192, 360)]),
            MenuImage((480, 148), self.item_imgs[2], scroll=[(0, 0), (320, 159), 160, 40, pg.Rect(448, 0, 192, 360)]),
            MenuImage((480, 308), self.item_imgs[3], scroll=[(0, 0), (320, 160), 160, 40, pg.Rect(448, 0, 192, 360)]),
            # Arrows
            # The only attributes checked are the ones in the dict, so the others are not needed
            Button(self, 1, (528, 124), self.arrow_imgs[0],
                   code='pg.event.post(pg.event.Event(pg.MOUSEWHEEL, {"x": 0, "y": 1}))'),
            Button(self, 1, (528, 288), self.arrow_imgs[1],
                   code='pg.event.post(pg.event.Event(pg.MOUSEWHEEL, {"x": 0, "y": -1}))'),

            # Images
            MenuImage((0, 64), self.constant_shop_gui_img),  # Frame
            # Top bar with text
            MenuImage((0, 0), render_menu_top_bar('Shop', self.font)),
            MenuImage((508, 0), center_word_on_image(render_rect((3, 3, 3), pg.Rect(
                # Page Number
                508, 0, 72, 60)), self.surface_ratio[0]**-1, [self.font.render('1', 0, (255, 255, 255), bgcolor=(3, 3, 3))])),

            # Exit button
            Button(self, 1, (8, 8), self.shop_exit_button_imgs, code=shop_exit_button_code),

            # Page flip buttons
            # event post so that the button menu updates
            Button(self, 1, (580, 8), self.switch_imgs[0], code=right_arrow_code),
            Button(self, 0, (456, 8), self.switch_imgs[1], code=left_arrow_code),

        ]),
            Menu(self, button_list=[
                # Shop items
                MenuImage((480, 148), self.upgrade_imgs[0], scroll=[(0, 0), (0, 160), 160, 40, pg.Rect(448, 0, 192, 360)]),
                MenuImage((480, 308), self.upgrade_imgs[1], scroll=[(0, 0), (0, 160), 160, 40, pg.Rect(448, 0, 192, 360)]),
                # Arrows
                # The only attributes checked are the ones in the dict, so the others are not needed
                Button(self, 1, (528, 124), self.arrow_imgs[0],
                       code='pg.event.post(pg.event.Event(pg.MOUSEWHEEL, {"x": 0, "y": 1}))'),
                Button(self, 1, (528, 288), self.arrow_imgs[1],
                       code='pg.event.post(pg.event.Event(pg.MOUSEWHEEL, {"x": 0, "y": -1}))'),
                # Images
                # Frame
                MenuImage((0, 64), self.constant_shop_gui_img),
                # Top bar with text
                MenuImage((0, 0), render_menu_top_bar('Shop', self.font)),
                MenuImage((508, 0), center_word_on_image(render_rect((3, 3, 3), pg.Rect(
                    # Page Number
                    508, 0, 72, 60)), self.surface_ratio[0]**-1, [self.font.render('2', 0, (255, 255, 255), bgcolor=(3, 3, 3))])),
                # Exit button
                Button(self, 1, (8, 8), self.shop_exit_button_imgs, code=shop_exit_button_code),
                # Page flip buttons
                Button(self, 0, (580, 8), self.switch_imgs[0], code=right_arrow_code),
                # event post so that the button menu updates
                Button(self, 1, (456, 8), self.switch_imgs[1], code=left_arrow_code),
            ]),
            ]
        # upgrade shop data V
        # first list is Special cookies (price first, then name of cookie), second is constant cookies 
        self.upgrade_data = [[(10**6, 'Stone'), (10**9, 'Bronze'), (10**12, 'Silver'), (10**15, 'Gold'), (10**18, 'Emerald')],
                             [(10**6, 6, 30), (10**9, 6, 25), (10**12, 5, 25), (10**15, 5, 20), (10**18, 4, 20),
                              (10**21, 4, 15), (10**24, 3, 15), (10**27, 3, 10), (10**30, 2, 10), (10**33, 2, 5)]]
        # overall shop data V
        # the first 2 indexes are for menus, the indexes inside of them is for the items; the first index in the item is the cost and the second index in the item is the value of what it gives,  and the third is what it gives (in save data terms)
        self.shop_data = [[(100, 1, 'auto_harvesters'), (100, 10, 'cookie_tree_values'), (10, 1, 'cookies_per_click'), (25, 1, 'cookies_per_second')],
                          [[self.upgrade_data[0][self.save_data['special_cookies_level']][0] if self.save_data['special_cookies_level'] < len(self.upgrade_data[0]) else 0, 1, 'special_cookies_level'],
                           [self.upgrade_data[1][self.save_data['constant_cookies_level']][0] if self.save_data['constant_cookies_level'] < len(self.upgrade_data[1]) else 0, 1, 'constant_cookies_level']]
                          ]

        buy_button_code = 'self.game.save_data["score"] -= self.game.shop_data[self.game.current_shop_menu[0]][self.game.current_shop_menu[1]][0]' \
                          ' * (1 if self.game.current_shop_menu[0] else self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]])\n' \
                          'self.game.save_data[self.game.shop_data[self.game.current_shop_menu[0]][self.game.current_shop_menu[1]][2]] += self.game.shop_data[self.game.current_shop_menu[0]][self.game.current_shop_menu[1]][1]' \
                          ' * (1 if self.game.current_shop_menu[0] else self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]])\n' \
                          'self.game.update_score_render(); self.game.set_button_clickable()'
        
        # meant to only be executed in the item shop, not the upgrade shop
        bulk_button_code = 'text = scientific_notation(self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]], self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]] >= 1000000000)\n' \
                           'self.game.bulk_buy_menu.button_list[1].text = text\n' \
                           'self.game.bulk_buy_menu.button_list[1].cursor_pos = len(text); self.game.bulk_buy_menu.on = 1;\n' \
                           'pg.key.set_repeat(400, 60); pg.key.start_text_input()\n' \
                           'for i in range(1, 3): self.game.shop_button_menu_list[self.game.current_shop_menu[0]][self.game.current_shop_menu[1]].button_list[i].clickable = 0'

        buy_button_code_split = buy_button_code.splitlines() # for tree buy button code

        

        self.shop_button_menu_list = [
            [
                Menu(self, button_list=[
                    MenuImage((0, 64), center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 296)), self.surface_ratio[0]**-1,
                                                            [self.font.render('Auto Harvester', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.small_font.render('Automatically harvests a tree for you whenever it grows a cookie. These are produced by Orpantine Inventions Limited.',
                                                                                    0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.font.render(f'Costs {self.shop_data[0][0][0]} cookies.', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],
                                                            pos=['center', 0]), scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)]),

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width(
                    ) + 16)) // -2), 328), self.buy_button_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)], code=f'{buy_button_code}; self.game.auto_harvest()'),
                    # buy_button_code should normally be at the end of the string (sets stuff up for next transaction), but this time it should be at the start ^

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width() + 16)) // -2) +
                                     self.buy_button_imgs['image'].get_width() + 16, 328), self.buy_button_number_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)], code=bulk_button_code),

                ]),

                Menu(self, button_list=[
                    # render_rect with black makes a clear background, 104 because of the scale factor
                    MenuImage((0, 64), center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 296)), self.surface_ratio[0]**-1,
                                                            [self.font.render('Cookie Tree', 0, (255, 255, 255), bgcolor=(0, 0, 0), wraplength=104),
                                                             self.small_font.render('Grows 10 cookies every day even while you are offline. These are produced by the Treevest Tree Company.',
                                                                                    0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.font.render(f'Costs {self.shop_data[0][1][0]} cookies.', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],
                                                            pos=['center', 0]), scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)]),

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width(
                        # adding 16 for the gap in between the buttons
                    ) + 16)) // -2), 328), self.buy_button_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)],
                           code=f'{buy_button_code_split[0]}; self.game.save_data["cookie_tree_values"][0] += self.game.config_data["item_shop_buy_numbers"][1]; {buy_button_code_split[2]}'),

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width() + 16)) // -2) +
                                     self.buy_button_imgs['image'].get_width() + 16, 328), self.buy_button_number_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)], code=bulk_button_code),
                ]),
                Menu(self, button_list=[
                    MenuImage((0, 64), center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 296)), self.surface_ratio[0]**-1,
                                                            [self.font.render('Oven', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.small_font.render('The basic oven. It Bakes 1 dollop of cookiedough into a cookie whenever you click. These are produced by the Voven Oven Company.',
                                                                                    0, (255, 255, 255), bgcolor=(0, 0, 0), wraplength=104),
                                                             self.font.render(f'Costs {self.shop_data[0][2][0]} cookies.', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],
                                                            pos=['center', 0]), scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)]),

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width(
                    ) + 16)) // -2), 328), self.buy_button_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)],
                           code=f'self.game.normal_indicator_texts[0] = pg.transform.scale_by(self.game.small_font.render(f"+{{scientific_notation(self.game.save_data["cookies_per_click"], self.game.save_data["cookies_per_click"] >= 1000000)}}", 0, (255, 255, 255), wraplength=32, bgcolor=(0, 0, 0)), (4, 4)); {buy_button_code}'),

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width() + 16)) // -2) +
                                     self.buy_button_imgs['image'].get_width() + 16, 328), self.buy_button_number_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)], code=bulk_button_code),

                ]),
                Menu(self, button_list=[
                    MenuImage((0, 64), center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 296)), self.surface_ratio[0]**-1,
                                                            [self.font.render('Perpetual Cog', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.small_font.render('An infinitely running cog that can power ovens indefinitely. Only works while you are online. These are produced by Orpantine Inventions Limited.',
                                                                                    0, (255, 255, 255), bgcolor=(0, 0, 0), wraplength=104),
                                                             self.font.render(f'Costs {self.shop_data[0][3][0]} cookies.', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],
                                                            pos=['center', 0]), scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)]),

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width(
                    ) + 16)) // -2), 328), self.buy_button_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)],
                           code='self.game.save_data["cookies_per_click"] -= self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]]\n' \
                                'self.game.normal_indicator_texts = [pg.transform.scale_by(self.game.small_font.render(f"+{scientific_notation(self.game.save_data["cookies_per_click"], self.game.save_data["cookies_per_click"] >= 1000000)}", 0, (255, 255, 255), wraplength=32, bgcolor=(0, 0, 0)), (4, 4)),\n' \
                                                            f'pg.transform.scale_by(self.game.small_font.render(f"+{{scientific_notation(self.game.save_data["cookies_per_second"], self.game.save_data["cookies_per_second"] >= 1000000)}}", 0, (255, 255, 255), wraplength=32, bgcolor=(0, 0, 0)), (4, 4))]; {buy_button_code}'),

                    Button(self, 1, (-((448 - (self.buy_button_imgs['image'].get_width() + self.buy_button_number_imgs['image'].get_width() + 16)) // -2) +
                                     self.buy_button_imgs['image'].get_width() + 16, 328), self.buy_button_number_imgs, scroll=[(0, 0), (0, 64), 4, 32, pg.Rect(0, 64, 448, 296)], code=bulk_button_code),

                ]),
            ],
            [
                Menu(self, button_list=[
                    MenuImage((0, 64), center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 400)), self.surface_ratio[0]**-1,
                                                            [self.font.render('Special Cookies', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.small_font.render('Special cookies are cookies that appear rarely. When one is clicked, it gives much more cookies than when you click the normal cookie.', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.font_center.render(f'Current Tier:\n{arabic_to_roman(self.save_data['special_cookies_level'])}. {(self.upgrade_data[0][self.save_data['special_cookies_level'] - 1][1] if self.save_data['special_cookies_level'] else 'No Special')} Cookie\n' \
                                                                                     f'{f'Next Tier Cost:\n{scientific_notation(self.shop_data[1][0][0], self.shop_data[1][0][0] >= 10**6)} Cookies' if self.save_data['special_cookies_level'] < len(self.upgrade_data[0]) else 'You are at the maximum tier.'}', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],
                                                            pos=['center', 0]), scroll=[(0, 0), (0, 208), 4, 32, pg.Rect(0, 64, 448, 296)]),
                                                            
                    Button(self, 1, (-((448 - self.buy_button_imgs['image'].get_width()) // -2), 472), self.buy_button_imgs, scroll=[(0, 0), (0, 208), 4, 32, pg.Rect(0, 64, 448, 296)],
                           code=f'{buy_button_code}; self.game.shop_data[1][0][0] = self.game.upgrade_data[0][self.game.save_data["special_cookies_level"]][0] if self.game.save_data["special_cookies_level"] < len(self.game.upgrade_data[0]) else 0\n' \
                                 'self.game.special_cookie.images = self.game.special_cookie_imgs[self.game.save_data["special_cookies_level"] - 1] \n' \
                                 'self.game.special_cookie_eating_animation.images = self.game.special_cookie_eating_animation_imgs[self.game.save_data["special_cookies_level"] - 1]\n' \
                                 'self.game.shop_button_menu_list[1][0].button_list[0].image = ' \
                                 'center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 400)), self.game.surface_ratio[0]**-1,\n' \
                                                      '[self.game.font.render("Special Cookies", 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),\n' \
                                                       'self.game.small_font.render("Special cookies are cookies that appear rarely. When one is clicked, it gives much more cookies than when you click the normal cookie.", 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),\n' \
                                                       'self.game.font_center.render(f"Current Tier:\\n{arabic_to_roman(self.game.save_data["special_cookies_level"])}. {(self.game.upgrade_data[0][self.game.save_data["special_cookies_level"] - 1][1] if self.game.save_data["special_cookies_level"] else "No Special")} Cookie\\n"' \
                                                                                    'f"{(f"Next Tier Cost:\\n{scientific_notation(self.game.shop_data[1][0][0], self.game.shop_data[1][0][0] >= 10**6)} Cookies" if self.game.save_data["special_cookies_level"] < len(self.game.upgrade_data[0]) else "You are at the maximum tier.")}", 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],'
                                                      'pos=["center", 0])'),

                ]),
                Menu(self, button_list=[
                    MenuImage((0, 64), center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 400)), self.surface_ratio[0]**-1,
                                                            [self.font.render('Constant Cookies', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.small_font.render('Constant Cookie bonuses are given when you click the cookie consistently over a certain amount of time.', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),
                                                             self.font_center.render(f'Current Tier:\n{arabic_to_roman(self.save_data['constant_cookies_level'])}. {f'Bonus awarded if you click {self.upgrade_data[1][self.save_data['constant_cookies_level'] - 1][1]} clicks per second for {self.upgrade_data[1][self.save_data['constant_cookies_level'] - 1][2]} seconds.'
                                                                                     if self.save_data['constant_cookies_level'] else 'No Bonuses Possible.'}\n{f'Next Tier Cost:\n{scientific_notation(self.shop_data[1][1][0], self.shop_data[1][1][0] >= 10**6)} Cookies'
                                                                                     if self.save_data['constant_cookies_level'] < len(self.upgrade_data[1]) else 'You are at the maximum tier.'}', 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],
                                                            pos=['center', 0]), scroll=[(0, 0), (0, 208), 4, 32, pg.Rect(0, 64, 448, 296)]),

                    Button(self, 1, (-((448 - self.buy_button_imgs['image'].get_width()) // -2), 472), self.buy_button_imgs, scroll=[(0, 0), (0, 208), 4, 32, pg.Rect(0, 64, 448, 296)],
                           code=f'{buy_button_code}; self.game.shop_data[1][1][0] = self.game.upgrade_data[1][self.game.save_data["constant_cookies_level"]][0] if self.game.save_data["constant_cookies_level"] < len(self.game.upgrade_data[1]) else 0\n' \
                                 'self.game.shop_button_menu_list[1][1].button_list[0].image = ' \
                                 'center_word_on_image(render_rect((0, 0, 0), pg.Rect(0, 64, 448, 400)), self.game.surface_ratio[0]**-1,\n' \
                                                     '[self.game.font.render("Constant Cookies", 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),\n' \
                                                      'self.game.small_font.render("Constant Cookie bonuses are given when click the cookie consistently over a certain amount of time.", 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0)),\n' \
                                                      'self.game.font_center.render(f"Current Tier:\\n{arabic_to_roman(self.game.save_data["constant_cookies_level"])}. {f"Bonus awarded if you click {self.game.upgrade_data[1][self.game.save_data["constant_cookies_level"] - 1][1]} clicks per second for {self.game.upgrade_data[1][self.game.save_data["constant_cookies_level"] - 1][2]} seconds."\n' \
                                                                                   'if self.game.save_data["constant_cookies_level"] else "No Bonuses Possible."}\\n{f"Next Tier Cost:\\n{scientific_notation(self.game.shop_data[1][1][0], self.game.shop_data[1][1][0] >= 10**6)} Cookies"\n' \
                                                                                   'if self.game.save_data["constant_cookies_level"] < len(self.game.upgrade_data[1]) else "You are at the maximum tier."}", 0, (255, 255, 255), wraplength=104, bgcolor=(0, 0, 0))],\n' \
                                                     'pos=["center", 0])')
                ]),
            ],
        ]

        # posts an event so that the menu starts rendering
        self.shop_open_button = Button(self, 1, (-((self.cookie_imgs['image'].get_width() - (self.shop_open_button_imgs['image'].get_width() + self.farm_open_button_imgs['image'].get_width() + 16)) // -2) + 96, 260), self.shop_open_button_imgs,
                                       code='self.game.shop_list[0].on = 1; pg.event.post(pg.event.Event(pg.MOUSEWHEEL, {"x": 0, "y": 0})); self.game.set_button_clickable()')
        self.farm_open_button = Button(self, 1, (-((self.cookie_imgs['image'].get_width() - (self.shop_open_button_imgs['image'].get_width() + self.farm_open_button_imgs['image'].get_width() + 16)) // -2) + self.shop_open_button_imgs['image'].get_width() + 16 + 96, 260), self.farm_open_button_imgs, code='self.game.farm_menu.on = 1')

        # a variable telling the index which menu is on. the first number is the shop that is open, and the second is the menu that is opened.
        self.current_shop_menu = [0, 2]
        # Cookie
        self.cookie = Button(self, 1, (96, 88), self.cookie_imgs, code='self.game.save_data["score"] += self.game.save_data["cookies_per_click"]\n' \
                                                                       'self.game.save_data["total_baked_cookies"] += self.game.save_data["cookies_per_click"]\n' \
                                                                       'self.game.update_score_render()\n' \
                                                                       'self.game.constant_cookies_stats[0] += 1 if self.game.save_data["constant_cookies_level"] else 0\n' \
                                                                       'self.game.cookie_indicators.append(MenuImage(((pg.mouse.get_pos()[0] - self.game.normal_indicator_texts[0].get_width() / 2) // self.game.surface_ratio[0]**-1 * self.game.surface_ratio[0]**-1,\n' \
                                                                                                                     '(pg.mouse.get_pos()[1] - self.game.normal_indicator_texts[0].get_height()) // self.game.surface_ratio[0]**-1 * self.game.surface_ratio[0]**-1), self.game.normal_indicator_texts[0].copy(), colorkey=(0, 0, 0)))')
        self.special_cookie = Button(self, 0, (640, 116), self.special_cookie_imgs[self.save_data['special_cookies_level'] - 1], code='self.game.update_score_render()\n' \
                                                                                                                                      'self.game.special_cookie_state = 2\n' \
                                                                                                                                      'self.game.special_cookie_eating_animation.render_pos = list(self.game.special_cookie.render_pos)\n' \
                                                                                                                                      'self.game.special_cookie_cookiefall.button_list[0].render_pos = [0, -1440]\n' \
                                                                                                                                      'self.game.special_cookie_cookiefall.button_list[1].render_pos = [0, -2160]\n' \
                                                                                                                                      'self.game.special_cookie_cookiefall.button_list[2].render_pos = [0, -2880]')

        self.special_cookie_eating_animation = Animation((0, 0), self.special_cookie_eating_animation_imgs[self.save_data['special_cookies_level'] - 1], 15, update_style='disappear')

        self.special_cookie_cookiefall = Menu(self, button_list=[MenuImage((0, 0), load_img('cookie/special/cookiefall/back.png', (640, 1440))),
                                                                 MenuImage((0, 0), load_img('cookie/special/cookiefall/middle.png', (640, 2160))),
                                                                 MenuImage((0, 0), load_img('cookie/special/cookiefall/front.png', (640, 2880)))])

        self.special_cookie_state = 0

        # below, in the codes, i use int() twice just in case (becaues i use max())
        self.bulk_buy_menu = Menu(self, (pg.Surface(self.screen_size), 160, (0, 0, 0)), button_list=[
            MenuImage((f'{self.screen_size[0]};{int(self.surface_ratio[0]**-1)}', 64), small_font_scaled.render(
                'Enter the amount (number or mathematical expression) to buy when pressing the "buy" button.', 0, (255, 255, 255), bgcolor=(0, 0, 0), wraplength=592), colorkey=(0, 0, 0)),

            TextBox(self, 1, (20, 180), {'image': render_rect((3, 3, 3), pg.Rect(0, 0, 600, 44), outline_color=(255, 255, 255), outline_width=4)}, [
                    small_font_scaled, 0, (255, 255, 255), None, 0], limit=36, text_pos=[8, 0], enter_code='self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]] = int((max(math_eval(self.text, 1, int), 1))); self.text = scientific_notation(math_eval(self.text, 1, int));'),
            Button(self, 1, (-((self.screen_size[0] - (self.save_button_imgs['image'].get_width() + self.clear_button_imgs['image'].get_width(
                # save button
            ) + 16)) // -2), 240), self.save_button_imgs, code='self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]] = int(max(math_eval(self.game.bulk_buy_menu.button_list[1].text, 1, int), 1)); self.game.save_config_data_to_file()\n' \
                                                               'self.game.bulk_buy_menu.button_list[1].text = scientific_notation(self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]], self.game.config_data["item_shop_buy_numbers"][self.game.current_shop_menu[1]] >= 1000000)'),

            Button(self, 1, (-((self.screen_size[0] - (self.save_button_imgs['image'].get_width() + self.clear_button_imgs['image'].get_width() + 16)) // -2) + self.save_button_imgs['image'].get_width() + 16, 240),
                   # clear button
                   self.clear_button_imgs, code='self.game.bulk_buy_menu.button_list[1].text = ""; self.game.bulk_buy_menu.button_list[1].cursor_pos = 0'),

            # Top bar with text
            MenuImage((0, 0), render_menu_top_bar('Bulk', self.font)),

            # Exit button
            Button(self, 1, (8, 8), self.shop_exit_button_imgs, 
                   code='self.game.bulk_buy_menu.on = 0; self.game.shop_button_menu_list[self.game.current_shop_menu[0]][self.game.current_shop_menu[1]].button_list[2].clickable = 1; self.game.set_button_clickable(); pg.key.set_repeat(); pg.key.stop_text_input()'),
            ])

        # code for trees in farm
        self.tree_code = 'for button in self.game.farm_menu.button_list[self.game.farm_menu.button_list.index(self):]: button.render_pos[0] = button.pos[0] + 160\n' \
                         'cookies_gained = last_index_greater_than_zero(self.game.save_data["cookie_tree_values"])\n' \
                         'if sum(self.game.save_data["cookie_tree_values"][1:]) <= 4: del self.game.farm_menu.button_list[-1]\n' \
                         'self.game.save_data["score"] += cookies_gained\n' \
                         'self.game.save_data["total_baked_cookies"] += cookies_gained\n' \
                         'self.game.save_data["cookie_tree_values"][cookies_gained] -= 1\n' \
                         'self.game.save_data["cookie_tree_values"][0] += 1\n' \
                         'self.game.update_tree_farm()\n' \
                         'self.game.update_score_render()'
         # for 2nd line ^: removes a full day if greater;  rest if less

        self.farm_menu = Menu(self, (pg.Surface(self.screen_size), 160, (0, 0, 0)), button_list=[
            # Top bar with text
            MenuImage((0, 0), render_menu_top_bar('Farm', self.font)),
            # Exit button
            Button(self, 1, (8, 8), self.shop_exit_button_imgs, code='self.game.farm_menu.on = 0'),
            # top text
            MenuImage((f'{self.screen_size[0]};{int(self.surface_ratio[0]**-1)}', 64), small_font_scaled.render(
                'Click a tree to harvest it.', 0, (255, 255, 255), bgcolor=(0, 0, 0), wraplength=640), colorkey=(0, 0, 0)),

            # Tree Box
            MenuImage((-4, 120), render_rect((3, 3, 3), pg.Rect(0, 0, 648, 160), outline_color=(255, 255, 255), outline_width=4)),
            # bottom text
            MenuImage((f'{self.screen_size[0]};{int(self.surface_ratio[0]**-1)}', 280), small_font_scaled.render(
                'If there are no trees, none have grown yet.', 0, (255, 255, 255), bgcolor=(0, 0, 0), wraplength=640), colorkey=(0, 0, 0)),

            ])
        self.cookie_grow_seconds = 8640 # the amount of seconds for one cookie to grow in cookie trees

        # Cookies per day check
        trees = sum(self.save_data['cookie_tree_values'])
        if trees:
            self.save_data['cookies_per_day_counter'] += int(time.time() - self.save_data['last_logout'])
            counter = divmod(int(self.save_data['cookies_per_day_counter']), int(self.cookie_grow_seconds))
            # ^ first is the number of max iterations, next is the cookies_per_day_coounter after procesesing

            if self.save_data['auto_harvesters']:
                # tree_value_loop_list is a list that the tree list will eventually become when shifted and harvested enough times
                # this is so that there is not that much unnecessary iterating (1.7 sec to 0.004 sec)
                # after the iteration, I change the score using a calculation
                tree_value_loop_list = [0] * 11
                auto_harvester_numbers_in_list = min(10, trees // self.save_data['auto_harvesters'])
                for i in range(auto_harvester_numbers_in_list):
                    tree_value_loop_list[i] = self.save_data['auto_harvesters']
                tree_value_loop_list[auto_harvester_numbers_in_list] = max(trees % self.save_data['auto_harvesters'], trees - self.save_data['auto_harvesters'] * 10)

                for i in range(counter[0]):
                    self.shift_tree_farm()
                    self.auto_harvest(change_score=0)
                    if self.save_data['cookie_tree_values'] == tree_value_loop_list:
                        break
                self.save_data['score'] += min(self.save_data['auto_harvesters'], trees) * counter[0]
                self.save_data['total_baked_cookies'] += min(self.save_data['auto_harvesters'], trees) * counter[0]
            else:
                for i in range(min(counter[0], 10)):
                    self.shift_tree_farm()

            self.save_data['cookies_per_day_counter'] = counter[1]
            self.update_tree_farm()
        self.update_score_render()
        
        # reminder: font height (before scaling) is 9; for centering, use wraplength to center
        # reminder: make sure gap between bottom of screen and bottom of text is 4 (pre-scale) pixels
        cutscene_finish_code = 'self.game.save_data["last_cutscene"] += 1'
        self.cutscenes = {
                'intro': Slideshow(self, cutscene_list=(
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 36), create_dialogue_animation(
                        'Fran Sancisco, Falicornia\n80 Years ago',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3))),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 68), create_dialogue_animation(
                        'Sir Carl Dough III was in his office when he heard the rupture.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/1.png', (152, 60))),)),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 59), create_dialogue_animation(
                        'He walked outside and saw a giant mound made of... well... brown goop. It seemed to grow out of the water.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/2.png', (152, 51))),)),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 59), create_dialogue_animation(
                        'As the owner of Bluever, a shipping company, Sir Dough commanded an idle ship to figure out what the mound was.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/3.png', (152, 51))),)),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 59), create_dialogue_animation(
                        'While most thought it was poop, one brave mariner decided to go near it. He discovered that it was cookiedough.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/4.png', (152, 51))),)),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 59), create_dialogue_animation(
                        'Sir Dough immediately started forming a cookie empire with his all-new salt-water cookies.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/5.png', (152, 51))),)),

                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 36), create_dialogue_animation(
                        'Fran Sancisco, Falicornia\nPresent Day',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3))),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 59), create_dialogue_animation(
                        'Cookies are now a currency used everywhere around the world. Dough\'s Salt-water Cookies are worth the most.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/7.png', (152, 51))),)),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 59), create_dialogue_animation(
                        'You have just inherited Sir Dough\'s empire, as the grandson of the legendary Sir Carl Dough III.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/8.png', (152, 51))),)),
                    Cutscene(self, Animation((f'{self.surface_size[0]};1', 59), create_dialogue_animation(
                        'All his machines mysteriously exploded before he passed away, though, so you have to start fresh.',
                        [small_font_center, 0, (255, 255, 255), (3, 3, 3), 144]), 5), sound=self.sfx['dialogue'], background=(pg.Surface(self.surface.get_size()), None, (3, 3, 3)),
                             button_list=(MenuImage((4, 4), load_img('cutscenes/intro/9.png', (152, 51))),)),

                    ), control_keys=(pg.K_RIGHT, pg.K_LEFT, pg.K_ESCAPE), transition_frames=60, auto_time=69, finish_code=cutscene_finish_code),
                
                    }

        self.cutscene_counts = [
                (0, 'intro'),

                ]
        self.check_cutscenes()

        # the hierarchy of pressing escape. if bulk buy menu and item shop are both open, bulk buy menu closes when escape is pressed
        # highest index will close last
        # only for menus that close individually. if there are sub menus that close alongisde a menu, put that in the code
        self.menu_hierarchy = (((self.bulk_buy_menu, 'self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].button_list[2].clickable = 1; self.set_button_clickable(); pg.key.stop_text_input()'),),
                               ((self.shop_list[0], 'self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].on = 0'),
                                (self.shop_list[1], 'self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].on = 0'),
                                (self.farm_menu, '')))
        
        self.constant_cookies_stats = [0, 0]
        # the first number is the number of clicks clicked in the last second
        # the second is the number of consecutive seconds clicked so far with the needed cps
        # the third number is the total number of clicks clicked in the period,

        special_cookie_cookie_amount = math.ceil(self.save_data["cookies_per_click"]**(self.save_data["special_cookies_level"] / 2)) * 100000
        self.cookie_indicators = [] # list of current "+1" menuimages
        self.normal_indicator_texts = [pg.transform.scale_by(self.small_font.render(f'+{scientific_notation(self.save_data['cookies_per_click'], self.save_data['cookies_per_click'] >= 1000000)}', 0, (255, 255, 255), wraplength=32, bgcolor=(0, 0, 0)), (4, 4)),
                                       pg.transform.scale_by(self.small_font.render(f'+{scientific_notation(self.save_data['cookies_per_second'], self.save_data['cookies_per_second'] >= 1000000)}', 0, (255, 255, 255), wraplength=32, bgcolor=(0, 0, 0)), (4, 4)),
                                       pg.transform.scale_by(self.font.render(f'+{scientific_notation(special_cookie_cookie_amount, special_cookie_cookie_amount >= 1000000)}', 0, (255, 255, 255), wraplength=360, bgcolor=(0, 0, 0)), (4, 4))]
        
    def save_save_data_to_file(self: object) -> None:

        """Saves the player\'s save data to the data/save/save.json file"""

        self.save_data['last_logout'] = int(time.time())
        with open('data/save/save.json', 'w', encoding='UTF-8') as save_file:
            json.dump(self.save_data, save_file)

    def save_config_data_to_file(self: object) -> None:

        """Saves the player\'s config data to the data/save/config.json file"""

        with open('data/save/config.json', 'w', encoding='UTF-8') as config_file:
            json.dump(self.config_data, config_file)

    def update_score_render(self: object) -> None:

        """Updates the Cookie count render."""

        self.score_render = self.font.render(scientific_notation(self.save_data["score"], self.save_data['score'] >= 1000000), 0, (255, 255, 255))

    def update_tree_farm(self: object) -> None:

        """Updates the menu of the tree farm."""

        for i in range(len(self.farm_menu.button_list[5:]), int(min(4, sum(self.save_data["cookie_tree_values"][1:])))): # add tree buttons; adds remaining with the range thing;
            self.farm_menu.button_list.append(Button(self, 1, (12 + i * 160, 136), self.farm_tree_imgs, scroll=[(160, 160), (0, 0), 1, 0, 0], code=self.tree_code))
        # len(self.farm_menu.button_list[5:]) is the amount of trees that are in the menu

    def shift_tree_farm(self: object) -> None:

        """Shifts the tree farm values right once. This is grows one cookie on all trees except the ones that already have 10 cookies."""

        self.save_data['cookie_tree_values'][-1] += self.save_data['cookie_tree_values'][-2] 
        for i in range(len(self.save_data['cookie_tree_values']) - 2, 0, -1):
            self.save_data['cookie_tree_values'][i] = self.save_data['cookie_tree_values'][i - 1]
        self.save_data['cookie_tree_values'][0] = 0
    
    def auto_harvest(self: object,
                     change_score: int or bool=1) -> None:

        """
        Auto harvest all the trees that can be autoharvested.

           change_score
             tells whether to change the players score or not
        """

        trees_to_harvest = min(sum(self.save_data['cookie_tree_values'][1:]), self.save_data['auto_harvesters'])
        while trees_to_harvest:
            dex = last_index_greater_than_zero(self.save_data['cookie_tree_values']) # finds the amount of cookies per tree to harvest
            trees_just_harvested = min(self.save_data['cookie_tree_values'][dex], trees_to_harvest) # trees that will be just harvested
            if not change_score:
                self.save_data['score'] += trees_just_harvested * dex
                self.save_data['total_baked_cookies'] += trees_just_harvested * dex
            self.save_data['cookie_tree_values'][0] += trees_just_harvested
            self.save_data['cookie_tree_values'][dex] -= trees_just_harvested
            trees_to_harvest -= trees_just_harvested

    def set_button_clickable(self: object) -> None:

        """For each buy button in the shop, set the clickable value according to the user's amount of cookies."""

        for item_dex, item_data in enumerate(self.shop_data[0]):
            self.shop_button_menu_list[0][item_dex].button_list[1].clickable = self.save_data['score'] >= (
                item_data[0] * self.config_data['item_shop_buy_numbers'][item_dex])
        self.shop_button_menu_list[0][3].button_list[1].clickable = self.save_data['score'] >= (self.shop_data[0][3][0] * self.config_data['item_shop_buy_numbers'][3]) \
                and self.save_data['cookies_per_click'] > self.config_data['item_shop_buy_numbers'][3]
        # makes sure the player always has at least 1 non-automatic oven
        for item_dex, item_data in enumerate(self.shop_data[1]):
            self.shop_button_menu_list[1][item_dex].button_list[1].clickable = self.save_data[item_data[2]] < len(self.upgrade_data[item_dex]) \
                    and self.save_data['score'] >= self.upgrade_data[item_dex][self.save_data[item_data[2]]][0]

    def check_cutscenes(self: object) -> None:

        """Checks if a cutscene(s) should be ran."""

        for dex, item in enumerate(self.cutscene_counts):
            if dex > self.save_data['last_cutscene'] and self.save_data['total_baked_cookies'] >= item[0]:
                self.cutscenes[item[1]].run(self.surface, self.game_speed, self.screen)

    def run(self: object) -> None:

        """Runs the main game loop."""

        try:
            running = 1
            start_time = time.time()
            # delta_time = 1 / pg.display.get_current_refresh_rate() # for when it is vsync
            dot_shown = 1
            shop_background = pg.Surface(self.screen_size)  # so i can set alpha
            shop_background.set_alpha(160)
            bulk_textbox = self.bulk_buy_menu.button_list[1]
            shop_on = sum([shop.on for shop in self.shop_list])

            while running:

                delta_time = time.time() - start_time
                start_time = time.time()

                # the current cutscene that should be rendered on the screen (fade transition)
                current_screen_cutscene = self.cutscenes[self.cutscene_counts[self.save_data['last_cutscene']][1]]
                
                # event handling
                for event in pg.event.get():
                    current_screen_cutscene.handle_events(event)

                    if not self.bulk_buy_menu.on:
                        for shop in self.shop_list:
                            shop.handle_events(event)
                        self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].handle_events(event)
                    shop_on = sum([shop.on for shop in self.shop_list])
                    self.farm_menu.handle_events(event)
                    self.bulk_buy_menu.handle_events(event)
                    if event.type == self.second_timer:
                        if self.save_data['special_cookies_level']:
                            self.save_data['seconds_until_next_special_cookie'] -= 1
                            if self.save_data['seconds_until_next_special_cookie'] <= 0:

                                self.save_data['seconds_until_next_special_cookie'] = random.randint(600, 3600)

                                special_cookie_cookie_amount = math.ceil(self.save_data["cookies_per_click"]**(self.save_data["special_cookies_level"]**0.1)) * 100000
                                self.normal_indicator_texts[2] = pg.transform.scale_by(self.font.render(f'+{scientific_notation(special_cookie_cookie_amount, special_cookie_cookie_amount >= 1000000)}', 0, (255, 255, 255), wraplength=360, bgcolor=(0, 0, 0)), (4, 4))

                                # V 0 is off, 1 is started, 2 is clicked, 3 means the animation has starteed for self.special_cookie_state
                                self.special_cookie_state = 1
                        if self.save_data['constant_cookies_level']:
                            if self.constant_cookies_stats[0] >= self.upgrade_data[1][self.save_data['constant_cookies_level'] - 1][1]:
                                self.constant_cookies_stats[1] += 1
                                if self.constant_cookies_stats[1] >= self.upgrade_data[1][self.save_data['constant_cookies_level'] - 1][2]:
                                    bonus = self.save_data['cookies_per_click'] * 10**(self.save_data['constant_cookies_level']**0.5)
                                    # reward constant cookies bonus
                                    self.save_data['score'] += bonus

                                    constant_cookies_bonus_text = pg.transform.scale_by(self.font.render(f'BONUS!+{scientific_notation(bonus, bonus >= 1000000)}', 0, (255, 255, 255), wraplength=32, bgcolor=(0, 0, 0)), (4, 4))
                                    self.cookie_indicators.append(MenuImage(((self.cookie.images['image'].get_width() - constant_cookies_bonus_text.get_width()) / 2 //
                                                                   self.surface_ratio[0]**-1 * self.surface_ratio[0]**-1 + self.cookie.pos[0], pg.mouse.get_pos()[1] + 4), constant_cookies_bonus_text, colorkey=(0, 0, 0)))

                                    self.update_score_render()
                                    self.constant_cookies_stats[1] = 0
                            else:
                                self.constant_cookies_stats[1] = 0
                            self.constant_cookies_stats[0] = 0
                        if self.save_data['cookies_per_second']:
                            self.cookie_indicators.append(MenuImage((random.randint(43, 48) * self.surface_ratio[0]**-1, 96), self.normal_indicator_texts[1].copy(), colorkey=(0, 0, 0)))

                            # .copy() ^ so then the alpha value doesn't change for all of the texts when setting alpha
                            self.save_data['score'] += self.save_data['cookies_per_second']
                            self.save_data['total_baked_cookies'] += self.save_data['cookies_per_second']
                            self.update_score_render()
                            if not self.bulk_buy_menu.on:  # it won't update until the menu is exited
                                self.set_button_clickable()
                        if sum(self.save_data['cookie_tree_values']):
                            self.save_data['cookies_per_day_counter'] += 1
                            # the below loop shifts everything and grows each tree
                            if not (self.save_data['cookies_per_day_counter'] % self.cookie_grow_seconds):
                                self.shift_tree_farm()
                                self.auto_harvest()
                                self.update_tree_farm()
                                self.update_score_render()
                            self.save_data['cookies_per_day_counter'] %= self.cookie_grow_seconds
                        dot_shown = not dot_shown
                        self.save_save_data_to_file()

                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            for menu_list in self.menu_hierarchy:
                                if tuple((item[0].on for item in menu_list)) != (0,) * len(menu_list):
                                    for item in menu_list:
                                        item[0].on = 0
                                        exec(item[1])
                                        pg.event.post(pg.Event(pg.MOUSEWHEEL, {"x": 0, 'y': 0}))
                                        # posts an event to make sure shop_on becomes zero
                                    break

                    elif event.type == pg.MOUSEWHEEL:
                        for dex, menu in enumerate(self.shop_list):
                            if menu.on:
                                if pg.Rect(448, 0, 192, 360).collidepoint(pg.mouse.get_pos()) or (not event.y and not event.x):
                                    self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].on = 0
                                    self.current_shop_menu = [dex, int((148 - (max(menu.button_list[0].pos[1] - menu.button_list[0].scroll_opts[1][1], min(
                                        menu.button_list[0].pos[1] + menu.button_list[0].scroll_opts[1][0], menu.button_list[0].wanted_scroll_pos[1])))) / 160)]
                                    self.set_button_clickable()
                                    for button in self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].button_list:
                                        button.render_pos = button.pos.copy()
                                        button.wanted_scroll_pos = button.pos.copy()

                                # makes sure its turned on even when the mouse pos is not in the rectangle (like when you click the shop open button)
                                self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].on = 1

                    elif event.type == pg.WINDOWRESIZED:
                        start_time = time.time() # makes sure delta time doesn't become super big during next frame

                    elif event.type == pg.QUIT:
                        running = 0

                    self.cookie.handle_events(event)
                    self.special_cookie.handle_events(event)
                    self.shop_open_button.handle_events(event)
                    self.farm_open_button.handle_events(event)

                    self.shop_open_button.clickable = not (shop_on or self.farm_menu.on)
                    self.farm_open_button.clickable = not (shop_on or self.farm_menu.on)

                # Update
                self.cookie.clickable = not self.special_cookie.rect.collidepoint(pg.mouse.get_pos()) and not (shop_on or self.farm_menu.on)
                self.special_cookie.clickable = not (shop_on or self.farm_menu.on) and self.special_cookie_state == 1
                self.cookie.update(delta_time * self.game_speed)
                if self.special_cookie_state:
                    self.special_cookie.update(delta_time * self.game_speed)
                self.shop_open_button.update(delta_time * self.game_speed)
                self.farm_open_button.update(delta_time * self.game_speed)
                current_screen_cutscene.update(delta_time * self.game_speed)

                if not self.bulk_buy_menu.on:
                    for shop in self.shop_list:
                        shop.update(delta_time * self.game_speed)
                elif not bulk_textbox.focused:
                    bulk_textbox.focused = 1
                self.farm_menu.update(delta_time * self.game_speed)
                self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].update(
                    delta_time * self.game_speed)
                self.bulk_buy_menu.update(delta_time * self.game_speed)

                if self.special_cookie_cookiefall.on:
                    self.special_cookie_cookiefall.button_list[0].render_pos[1] += 12 * delta_time * self.game_speed
                    self.special_cookie_cookiefall.button_list[1].render_pos[1] += 18 * delta_time * self.game_speed
                    self.special_cookie_cookiefall.button_list[2].render_pos[1] += 24 * delta_time * self.game_speed
                    if self.special_cookie_cookiefall.button_list[0].render_pos[1] >= 360:
                        self.special_cookie_cookiefall.on = 0
                # Hands the special cookie moving across the screen / updating the animation
                if self.special_cookie_state:
                    if self.special_cookie.render_pos[0] <= -128 or (self.special_cookie_state == 3
                                                                     and not self.special_cookie_eating_animation.running
                                                                     and not self.special_cookie_cookiefall.on):

                        self.special_cookie_state = 0

                    if self.special_cookie_state == 1:
                        self.special_cookie.render_pos[0] -= 4 * delta_time * self.game_speed
                        self.special_cookie.render_pos[1] = 48 * math.sin((self.special_cookie.render_pos[0] - 640) / 64) + 116
                    elif self.special_cookie_state == 2 and self.special_cookie.rect.size == (128, 128):
                        self.special_cookie_state = 3
                        self.special_cookie.rect.x = self.special_cookie.pos[0]
                        self.special_cookie.rect.y = self.special_cookie.pos[1]
                        self.special_cookie.render_pos = list(self.special_cookie.pos)
                        self.special_cookie_eating_animation.running = 1
                        # when it's (128, 128), the images perfectly transition
                    elif self.special_cookie_state == 3:
                        self.special_cookie_eating_animation.update(delta_time * self.game_speed)
                        if not self.special_cookie_eating_animation.running and not self.special_cookie_cookiefall.on:
                            self.save_data["score"] += special_cookie_cookie_amount
                            self.save_data["total_baked_cookies"] += special_cookie_cookie_amount
                            self.update_score_render()
                            self.special_cookie_cookiefall.on = 1
                            self.cookie_indicators.append(MenuImage(((self.screen_size[0] - self.normal_indicator_texts[2].get_width()) / 2,
                                                                     (self.screen_size[1] - self.normal_indicator_texts[2].get_height()) / 2),
                                                                    self.normal_indicator_texts[2].copy(), colorkey=(0, 0, 0)))

                # Rendering
                self.surface.blit(self.background, (0, 0))
                self.surface.blit(self.earth_imgs[min(int(math.sqrt(self.save_data['total_baked_cookies']) // 10**15), 8)], (82, 2))
                if dot_shown:
                    self.surface.blit(self.red_dot, (85, 5))
                self.surface.blit(self.score_render, (int((self.cookie_imgs['image'].get_width() * self.surface_ratio[0] - self.score_render.get_width()) / 2 + self.cookie.pos[0] * self.surface_ratio[0]), 0))

                # Cutscene stuff
                self.screen.blit(pg.transform.scale(self.surface, self.screen_size), (0, 0))
                if (not (current_screen_cutscene.on
                         and (current_screen_cutscene.wanted_slide < len(current_screen_cutscene.cutscene_list)
                              or (current_screen_cutscene.transition_style == 'fade'
                                  and current_screen_cutscene.wanted_slide == len(current_screen_cutscene.cutscene_list)
                                  and current_screen_cutscene.transition_state == 1)))
                    or self.save_data['last_cutscene'] == -1):

                    self.cookie.render(self.screen)
                    self.shop_open_button.render(self.screen)
                    self.farm_open_button.render(self.screen)

                    self.special_cookie_cookiefall.render(self.screen)

                    for i in range(len(self.cookie_indicators) - 1, -1, -1):
                        alpha = self.cookie_indicators[i].image.get_alpha()
                        alpha = (255 if alpha == None else alpha)
                        self.cookie_indicators[i].update(delta_time * self.game_speed)
                        self.cookie_indicators[i].render_pos[1] -= delta_time * 48
                        self.cookie_indicators[i].image.set_alpha(alpha - delta_time * 196)
                        self.cookie_indicators[i].render(self.screen)
                        if alpha <= 0:
                            del self.cookie_indicators[i]
                    if self.special_cookie_state:
                        if self.special_cookie_state > 2:
                            self.special_cookie_eating_animation.render(self.screen)
                        else:
                            self.special_cookie.render(self.screen)


                    if shop_on: # I use this instead of setting the backgrounds so that images in the shop menu overlay the text, while the background doesn't
                        self.screen.blit(shop_background, (0, 0))
                    self.shop_button_menu_list[self.current_shop_menu[0]][self.current_shop_menu[1]].render(self.screen)
                    for shop in self.shop_list:
                        shop.render(self.screen)
                    self.farm_menu.render(self.screen)
                    self.bulk_buy_menu.render(self.screen)

                if (self.save_data['last_cutscene'] >= 0
                    and current_screen_cutscene.transition_style == 'fade'
                    and current_screen_cutscene.wanted_slide == len(current_screen_cutscene.cutscene_list)
                    and current_screen_cutscene.transition_state == -1):
                    
                    current_screen_cutscene.render(self.screen)

                pg.display.update()

        finally:
            self.save_save_data_to_file()
            self.save_config_data_to_file()
            pg.quit()


if __name__ == '__main__':
    Game().run()

