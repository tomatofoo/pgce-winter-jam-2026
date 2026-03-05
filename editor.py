import os
import time
import math
import copy
import json
from typing import Self
from numbers import Real

import pygame as pg
from pygame.typing import Point


def load_img(*args: str, size: Point=None) -> pg.Surface:
    img = pg.image.load(os.path.join('data', 'images', *args))
    if size is not None:
        img = pg.transform.scale(img, size)
    return img

def gen_tile_key(obj: Point):
    return f'{int(math.floor(obj[0]))};{int(math.floor(obj[1]))}'


class Game(object):

    _SCREEN_SIZE = (640, 480)
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
        pg.display.set_caption('Icebox Editor')
        self._running = 0

        pg.key.set_repeat(300, 75)
        
        self._tool = 'place' # place, remove, eyedropper
        self._pos = pg.Vector2(0, 0)
        self._zoom = 16
        
        self._textures = [
            load_img('obstacle.png'),
        ]
        self._tilemap = {}
        self._data = {
            'texture': 0,
            'lines': [
            ],
        }

    def _gen_map_pos(self: Self, screen_pos: Point) -> pg.Vector2:
        return (
            (screen_pos - pg.Vector2(self._screen.size) / 2)
            / self._zoom
            + self._pos
        )

    def _gen_screen_pos(self: Self, map_pos: Point) -> pg.Vector2:
        return (
            (map_pos - self._pos) * self._zoom
            + (self._screen.size[0] / 2, self._screen.size[1] / 2)
        )

    def _draw_grid(self: Self) -> None:
        origin = pg.Vector2(
            math.floor(self._pos[0] - self._SCREEN_SIZE[0] / 2 / self._zoom),
            math.floor(self._pos[1] - self._SCREEN_SIZE[1] / 2 / self._zoom),
        )

        width = int(self._SCREEN_SIZE[0] / self._zoom)
        height = int(self._SCREEN_SIZE[1] / self._zoom)

        for y in range(height + 2):
            for x in range(width + 2):
                tile = origin + (x, y)
                pg.draw.rect(
                    self._screen,
                    (255, 255, 255),
                    (self._gen_screen_pos(tile), (2, 2)),
                )

    def _draw_tiles(self: Self) -> None:
        origin = pg.Vector2(
            math.floor(self._pos[0] - self._SCREEN_SIZE[0] / 2 / self._zoom),
            math.floor(self._pos[1] - self._SCREEN_SIZE[1] / 2 / self._zoom),
        )
        width = int(self._SCREEN_SIZE[0] / self._zoom)
        height = int(self._SCREEN_SIZE[1] / self._zoom)

        for y in range(height + 2):
            for x in range(width + 2):
                tile = origin + (x, y)
                tile_key = gen_tile_key(tile)
                data = self._tilemap.get(tile_key)
                if data is not None:
                    texture = pg.transform.scale(
                        self._textures[data['texture']],
                        (self._zoom, self._zoom),
                    )
                    
                    self._screen.blit(texture, self._gen_screen_pos(tile))
                    
                    pos = self._gen_screen_pos(tile)
                    for line in data['lines']:
                        pg.draw.line(
                            self._screen,
                            (0, 0, 255),
                            pos + (line[0][0] * self._zoom, line[0][1] * self._zoom),
                            pos + (line[1][0] * self._zoom, line[1][1] * self._zoom),
                        )

    def _draw_tool(self: Self, tile: Point) -> None:
        screen_pos = self._gen_screen_pos(tile)
        if self._tool == 'place':
            surf = pg.transform.scale(
                self._textures[self._data['texture']],
                (self._zoom, self._zoom),
            )
            surf.set_alpha(128)
            self._screen.blit(surf, screen_pos)
            return None
        rect = (screen_pos, (self._zoom, self._zoom))
        if self._tool == 'remove':
            pg.draw.rect(self._screen, (255, 0, 0), rect, 1) 
        elif self._tool == 'eyedropper':
            pg.draw.rect(self._screen, (0, 255, 0), rect, 1)

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            keys = pg.key.get_pressed()
            mouse = pg.mouse.get_pressed()

            mouse_pos = pg.mouse.get_pos()
            tile = self._gen_map_pos(mouse_pos)
            tile = pg.Vector2(math.floor(tile[0]), math.floor(tile[1]))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_z:
                        self._zoom += 8
                    elif event.key == pg.K_x:
                        self._zoom = max(self._zoom - 4, 8)
                    elif event.key == pg.K_h:
                        self._data['texture'] = (
                            (self._data['texture'] - 1)
                            % len(self._textures)
                        )
                    elif event.key == pg.K_l:
                        self._data['texture'] = (
                            (self._data['texture'] + 1)
                            % len(self._textures)
                        )
                    elif event.key == pg.K_b:
                        self._tool = 'place'
                    elif event.key == pg.K_e:
                        self._tool = 'remove'
                    elif event.key == pg.K_i:
                        self._tool = 'eyedropper'
            
            # Update
            movement = (
                keys[pg.K_d] - keys[pg.K_a],
                keys[pg.K_s] - keys[pg.K_w],
            )
            speed = 8 if keys[pg.K_LSHIFT] else 4
            self._pos += (
                movement[0] / self._zoom * speed * rel_game_speed,
                movement[1] / self._zoom * speed * rel_game_speed,
            )
            if mouse[0]:
                key = gen_tile_key(tile)
                if self._tool == 'place':
                    self._tilemap[key] = copy.deepcopy(self._data)
                elif self._tool == 'remove':
                    try:
                        self._tilemap.pop(key)
                    except KeyError:
                        pass
                elif self._tool == 'eyedropper':
                    data = self._tilemap.get(key)
                    self._data = copy.deepcopy(data)
            
            # Render
            self._screen.fill((0, 0, 0))
            self._draw_grid()
            self._draw_tiles()
            self._draw_tool(tile)
            surf = pg.transform.scale(
                self._textures[self._data['texture']], (32, 32),
            )
            self._screen.blit(surf, (0, 0))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

