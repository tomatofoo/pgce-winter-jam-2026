import time
import math
from typing import Self
from numbers import Real

import pygame as pg
from pygame import mixer as mx
from pygame.typing import Point

from modules.utils import SMALL
from modules.utils import load_img
from modules.utils import load_sfx
from modules.utils import load_mus
from modules.utils import load_tilemap
from modules.level import Puck
from modules.level import Level
from modules.camera import Camera


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
            flags=self._SCREEN_FLAGS,
            vsync=self._settings['vsync']
        )
        pg.display.set_caption('Icebox')
        self._surface = pg.Surface(self._SURF_SIZE)
        self._running = 0
        
        self._state = 'tutorial'

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
        }

        self._sounds = {
            'bounce': load_sfx('bounce.mp3'),
            'die': load_sfx('die.mp3'),
            'launch': load_sfx('launch.mp3'),
        }
        
        self._puck = Puck(
            surfs=self._images['puck'],
            width=0.9,
            render_width=1,
            bounce_sound=self._sounds['bounce'],
            die_sound=self._sounds['die'],
        )
        self._level = Level(
            entities={self._puck},
            tilemap=load_tilemap(0),
            textures=(
                load_img('backgrounds', '1.png'),
                load_img('obstacles', 'square.png'),
                load_img('obstacles', 'triangle1.png'),
                load_img('obstacles', 'triangle2.png'),
                load_img('obstacles', 'triangle3.png'),
                load_img('obstacles', 'triangle4.png'),
            ),
        )
        self._camera = Camera(self._level, (0, 0))

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()
        
        while self._running:
            # Delta time
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            mouse = pg.mouse.get_pressed()
            mouse_pos = pg.mouse.get_pos()
            vector = (
                self._puck.pos
                - self._camera.gen_map_pos(
                    (mouse_pos[0] / self._SURF_RATIO[0],
                     mouse_pos[1] / self._SURF_RATIO[1]),
                    self._surface.size,
                )
            )
            if vector.magnitude() > 5: # cant scale zero vector
                vector.scale_to_length(5)
            can_launch = self._puck.speed < SMALL

            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif self._state == 'dead':
                    pass
                else:
                    if event.type == pg.MOUSEBUTTONUP and can_launch:
                        self._puck.velocity = (
                            vector * 0.1 if vector else pg.Vector2(0, 0)
                        )
                        sound = self._sounds['launch']
                        sound.set_volume(vector.magnitude())
                        sound.play()
            
            if self._state == 'dead':
                pass
            else:
                self._level.update(rel_game_speed)
                self._camera.update(rel_game_speed, self._puck.pos)

                # Render 
                self._camera.render(self._surface)
                if mouse[0] and self._puck.speed < SMALL:
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
                if can_launch:
                    self._surface.blit(
                        pg.transform.scale(
                            self._images['launch']['can'],
                            [self._camera.zoom * 2] * 2,
                        ),
                        (8 / self._SURF_RATIO[0], 8 / self._SURF_RATIO[1]),
                    )
                else:
                    self._surface.blit(
                        pg.transform.scale(
                            self._images['launch']['cant'],
                            [self._camera.zoom * 2] * 2,
                        ),
                        (8 / self._SURF_RATIO[0], 8 / self._SURF_RATIO[1]),
                    )

            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

