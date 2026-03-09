import time
import math
import random
from typing import Self
from numbers import Real

import pygame as pg
from pygame import mixer as mx
from pygame.typing import Point

from modules.utils import SMALL
from modules.utils import load_fnt
from modules.utils import load_img
from modules.utils import load_sfx
from modules.utils import load_mus
from modules.utils import load_tilemap
from modules.utils import gen_text_surf
from modules.utils import gen_text_button_surf
from modules.level import Puck
from modules.level import Boost
from modules.level import End
from modules.level import Level
from modules.camera import Camera
from modules.menu import Text
from modules.menu import Button
from modules.menu import Menu


# Sloppy coded but it's okay because it's a game jam
class Game(object):

    _SCREEN_SIZE = (960, 720)
    _SURF_RATIO = (2, 2)
    _SURF_SIZE = (int(_SCREEN_SIZE[0] / _SURF_RATIO[0]),
                  int(_SCREEN_SIZE[1] / _SURF_RATIO[1]))
    _SCREEN_FLAGS = pg.RESIZABLE | pg.SCALED
    _GAME_SPEED = 60

    def __init__(self: Self) -> None:
        pg.init()

        self._settings = {
            'vsync': 1,
        }
        self._screen = pg.display.set_mode(
            self._SCREEN_SIZE,
            flags=self._SCREEN_FLAGS, # flags don't really work in pygbag
            vsync=self._settings['vsync'], # not sure about vsync in pygbag
        )
        pg.display.set_caption('Icebox')
        self._surface = pg.Surface(self._SURF_SIZE)
        self._running = 0
        self._level_timer = 0
    
        self._state = 'tutorial' # tutorial, alive, dead, win, finish
        self._restarted = 0
        self._strokes = 0
        self._bounces = 0
        
        # Assets
        self._font = pg.font.SysFont('Arial', int(self._SURF_SIZE[1] / 15))
        self._images = {
            'launch': {
                'can': load_img('launch', 'can.png'),
                'cant': load_img('launch', 'cant.png'),
            },
            'puck': (
                load_img('puck', '1.png'),
                load_img('puck', '2.png'),
                load_img('puck', '3.png'),
                load_img('puck', '4.png'),
                load_img('puck', '5.png'),
                load_img('puck', '6.png'),
                load_img('puck', '7.png'),
                load_img('puck', '8.png'),
                load_img('puck', '9.png'),
                load_img('puck', '10.png'),
            ),
            'textures': (
                load_img('backgrounds', '1.png'),
                load_img('obstacles', 'square.png'),
                load_img('obstacles', 'triangle1.png'),
                load_img('obstacles', 'triangle2.png'),
                load_img('obstacles', 'triangle3.png'),
                load_img('obstacles', 'triangle4.png'),
                load_img('specials', 'boost_up.png'),
                load_img('specials', 'boost_down.png'),
                load_img('specials', 'boost_left.png'),
                load_img('specials', 'boost_right.png'),
                load_img('specials', 'end.png'),
            )
        }
        self._sounds = {
            'bounce': load_sfx('bounce.mp3'),
            'die': load_sfx('die.mp3'),
            'launch': load_sfx('launch.mp3'),
            'boost': load_sfx('boost.mp3'),
            'start': load_sfx('start.mp3'),
        }
        
        # Game Stuff
        ## Data
        # health amounts for each level
        # Also used to determine number of levels
        self._health = (
            20,
        )
        self._specials = {
            'boost_up': Boost('up', sound=self._sounds['boost']),
            'boost_down': Boost('down', sound=self._sounds['boost']),
            'boost_left': Boost('left', sound=self._sounds['boost']),
            'boost_right': Boost('right', sound=self._sounds['boost']),
            'end': End(),
        }
        self._level_number = 0
        self._puck = Puck(
            surfs=self._images['puck'],
            width=0.9,
            render_width=1,
            health=self._health[self._level_number],
        )
        self._level = Level(
            entities={self._puck},
            tilemap=load_tilemap(self._level_number),
            specials=self._specials,
            textures=self._images['textures'],
        )
        self._camera = Camera(self._level)
        
        # Menus
        self._init_menus()

    def _init_menus(self: Self) -> None:
        self._dead_widgets = {
            'strokes': Text(
                self._font,
                f'Strokes: {self._strokes}',
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.325),
            ),
            'bounces': Text(
                self._font,
                f'Bounces: {self._bounces}',
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.45),
            ),
        }
        self._dead_menu = Menu({
            Text(
                self._font,
                'YOU CRACKED!',
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.2),
            ),
            self._dead_widgets['strokes'],
            self._dead_widgets['bounces'],
            Button(
                gen_text_button_surf(self._font, 'Restart', (255, 0, 0)),
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.75),
                self._restart,
            )
        })

        self._win_widgets = {
            'strokes': Text(
                self._font,
                f'Strokes: {self._strokes}',
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.325),
            ),
            'bounces': Text(
                self._font,
                f'Bounces: {self._bounces}',
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.45),
            ),
        }
        self._win_menu = Menu({
            Text(
                self._font,
                'YOU BEAT THE LEVEL!',
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.2),
            ),
            self._win_widgets['strokes'],
            self._win_widgets['bounces'],
            Button(
                gen_text_button_surf(self._font, 'Next Level', (255, 0, 0)),
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.75),
                self._next_level,
            )
        })

    def _restart(self: Self) -> None:
        self._state = 'alive'
        self._strokes = 0
        self._bounces = 0
        self._puck.health = self._health[self._level_number]
        self._puck.pos = (0, 0)
        self._puck.velocity = (0, 0)
        self._puck.boost = (0, 0)
        self._level.tilemap = load_tilemap(self._level_number)
        self._restarted = 1
        self._sounds['start'].play()

    def _next_level(self: Self) -> None:
        self._restart()
        self._level_number += 1

    def _render_menu_bg(self: Self) -> None:
        bg = self._level.background
        if bg is not None:
            size = self._camera.zoom * self._level.tilemap['bg']['scale']
            bg = pg.transform.scale(bg, (size, size))
            offset = pg.Vector2(
                self._level_timer / 240 % 1 * size,
                self._level_timer / 240 % 1 * size
            )
            for y in range(-1, int(self._SURF_SIZE[1] / bg.height) + 1):
                for x in range(-1, int(self._SURF_SIZE[0] / bg.width) + 1):
                    self._surface.blit(bg, (x * size, y * size) + offset)

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        self._sounds['start'].play()
        
        while self._running:
            # Delta time
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED
            self._level_timer += rel_game_speed

            mouse = pg.mouse.get_pressed()
            mouse_pos = pg.mouse.get_pos()
            mouse_pos = (mouse_pos[0] / self._SURF_RATIO[0],
                         mouse_pos[1] / self._SURF_RATIO[1])
            vector = (
                self._puck.pos
                - self._camera.gen_map_pos(mouse_pos, self._surface.size)
            )
            if vector.magnitude() > 5: # cant scale zero vector
                vector.scale_to_length(5)
            can_launch = self._puck.speed < SMALL

            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif self._state == 'dead':
                    self._dead_menu.handle_event(event)
                elif self._state == 'win':
                    self._win_menu.handle_event(event)
                else:
                    if event.type == pg.MOUSEBUTTONDOWN:
                        self._restarted = 0
                        if self._state == 'tutorial':
                            self._state = 'alive'
                    elif (event.type == pg.MOUSEBUTTONUP
                        and can_launch
                        and not self._restarted):
                        self._strokes += 1
                        self._puck.health -= 5
                        self._puck.velocity = (
                            vector * 0.1 if vector else pg.Vector2(0, 0)
                        )
                        sound = self._sounds['launch']
                        sound.set_volume(vector.magnitude())
                        sound.play()
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_r:
                            self._restart()
            
            if self._state == 'dead':
                # Update
                self._dead_menu.update(rel_game_speed, mouse_pos, mouse)
                self._render_menu_bg()
                self._dead_menu.render(self._surface)
            elif self._state == 'win':
                self._win_menu.update(rel_game_speed, mouse_pos, mouse)
                self._render_menu_bg()
                self._win_menu.render(self._surface)
            else:
                # Update
                self._level.update(rel_game_speed)
                self._camera.update(rel_game_speed, self._puck.pos)

                if self._puck.bounced:
                    self._bounces += 1
                    sound = self._sounds['bounce']
                    sound.set_volume(self._puck.net_speed * 0.8)
                    sound.play()
                if self._puck.dead:
                    self._state = 'dead'
                    self._dead_widgets['strokes'].text = (
                        f'Strokes: {self._strokes}'
                    )
                    self._dead_widgets['bounces'].text = (
                        f'Bounces: {self._bounces}'
                    )
                    self._sounds['die'].play()
                elif self._level.specials['end'].touched:
                    self._state = 'win'
                    self._win_widgets['strokes'].text = (
                        f'Strokes: {self._strokes}'
                    )
                    self._win_widgets['bounces'].text = (
                        f'Bounces: {self._bounces}'
                    )
                    self._sounds['win'].play()


                # Render 
                self._camera.render(self._surface)
                if (mouse[0]
                    and self._puck.speed < SMALL
                    and not self._restarted):
                    size = int(self._camera.zoom / 8)
                    start_pos = self._camera.gen_screen_pos(
                        self._puck.pos, self._surface.size,
                    )
                    end_pos = start_pos - vector * self._camera.zoom
                    pg.draw.line( # Shadow
                        self._surface,
                        (0, 96, 0),
                        start_pos + (0, size),
                        end_pos + (0, size),
                        size,
                    )
                    pg.draw.line( # Actual Line
                        self._surface,
                        (0, 255, 0),
                        start_pos,
                        end_pos,
                        size,
                    )
                ## HUD
                offset = (8 / self._SURF_RATIO[0], 8 / self._SURF_RATIO[1])
                surf = gen_text_surf(self._font, str(self._puck.health))
                self._surface.blit(surf, offset)
                if can_launch: # Launch Indicator
                    surf = pg.transform.scale(
                        self._images['launch']['can'],
                        [self._camera.zoom * 2] * 2,
                    )
                    self._surface.blit(
                        surf,
                        (self._SURF_SIZE[0] - offset[0] - surf.width,
                         offset[1]),
                    )
                else:
                    surf = pg.transform.scale(
                        self._images['launch']['cant'],
                        [self._camera.zoom * 2] * 2,
                    )
                    self._surface.blit(
                        surf,
                        (self._SURF_SIZE[0] - offset[0] - surf.width,
                         offset[1]),
                    )
                if self._state == 'tutorial': # MAYBE REMOVE THIS
                    offset = (
                        (self._level_timer % 60 > 30) * self._camera.zoom / 8
                    )
                    surf = gen_text_surf(self._font, 'Stroke: -5')
                    self._surface.blit(
                        surf,
                        ((self._SURF_SIZE[0] - surf.width) / 2,
                         self._SURF_SIZE[1] * 0.3 + offset)
                    )
                    surf = gen_text_surf(self._font, 'Bounce: -1')
                    self._surface.blit(
                        surf,
                        ((self._SURF_SIZE[0] - surf.width) / 2,
                         self._SURF_SIZE[1] * 0.425 + offset)
                    )

            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

