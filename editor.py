import os
import time
import math
import copy
import json
from typing import Self
from typing import Optional
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

# Sloppy code because game jam
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
        self._running = 0

        pg.key.set_repeat(300, 75)
        self._font = pg.font.SysFont('Arial', 16)
        
        self._tool = 'place' # place, remove, eyedropper
        self._pos = pg.Vector2(0, 0)
        self._zoom = 16
        self._lines_dex = 0
        self._type_dex = 0

        self._number = 0
        self._unsaved = 0
        self._change_title()

        self._tilemap = {
            'bg': {
                'texture': -1,
                'scale': 4,
            },
        }
        self._textures = [
            load_img('backgrounds', 'level1.png'),
            load_img('obstacles', 'square.png'),
            load_img('obstacles', 'triangle1.png'),
            load_img('obstacles', 'triangle2.png'),
            load_img('obstacles', 'triangle3.png'),
            load_img('obstacles', 'triangle4.png'),
        ]
        self._lines = [
            (((0, 0), (1, 0)), # SQUARE
             ((1, 0), (1, 1)),
             ((1, 1), (0, 1)),
             ((0, 1), (0, 0))),
            (((0, 0), (0, 1)), # TRIANGLE1
             ((0, 1), (1, 1)),
             ((1, 1), (0, 0))),
            (((0, 1), (1, 1)), # TRIANGLE2
             ((1, 1), (1, 0)),
             ((1, 0), (0, 1))),
            (((1, 1), (1, 0)), # TRIANGLE3
             ((1, 0), (0, 0)),
             ((0, 0), (1, 1))),
            (((1, 0), (0, 0)), # TRIANGLE4
             ((0, 0), (0, 1)),
             ((0, 1), (1, 0))),
        ]
        self._types = [
            'normal',
            'end',
            'boost',
        ]
        self._data = {
            'texture': 1,
            'lines': self._lines[self._lines_dex],
            'type': 'normal',
        }

    def _change_title(self: Self) -> None:
        pg.display.set_caption('Icebox Editor' + '*' * self._unsaved)

    def _save(self: Self, path: str) -> None:
        with open(os.path.join('data', 'maps', path), 'w') as file:
            json.dump(self._tilemap, file)

    def _load(self: Self, path: str) -> None:
        try:
            with open(os.path.join('data', 'maps', path), 'r') as file:
                self._tilemap = json.load(file)
        except FileNotFoundError:
            pass

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
                    (0, 255, 255),
                    (self._gen_screen_pos(tile), (2, 2)),
                )

    def _draw_tile(self: Self,
                   pos: pg.Vector2,
                   data: Optional[dict],
                   alpha: Optional[int]=255,
                   size: Optional[int]=None) -> None:
        if data is not None:
            if size is None:
                size = self._zoom
            surf = pg.transform.scale(
                self._textures[data['texture']], (size, size),
            )
            tile_type = data['type']
            if tile_type == 'end':
                pg.draw.rect(
                    surf,
                    (0, 255, 0),
                    (0, 0, size / 2, size / 2),
                    3,
                )
            elif tile_type == 'boostleft':
                pass
            elif tile_type == 'boostright':
                pass
            elif tile_type == 'boostup':
                pass
            elif tile_type == 'boostdown':
                pass
            surf.set_alpha(alpha)
            self._screen.blit(surf, pos)
            # Drawn after because it might not appear on surf
            # alpha value is ignored for lines
            for line in data['lines']:
                pg.draw.line(
                    self._screen,
                    (255, 0, 255),
                    pos + (line[0][0] * size, line[0][1] * size),
                    pos + (line[1][0] * size, line[1][1] * size),
                    2,
                )

    def _draw_background(self: Self) -> None:
        self._screen.fill((0, 0, 0))
        data = self._tilemap['bg']
        if data['texture'] != -1:
            scale = data['scale']
            size = scale * self._zoom
            origin = pg.Vector2(
                (self._pos[0] - self._SCREEN_SIZE[0] / 2 / self._zoom)
                // scale * scale,
                (self._pos[1] - self._SCREEN_SIZE[1] / 2 / self._zoom)
                // scale * scale,
            )
            width = int(self._SCREEN_SIZE[0] / size)
            height = int(self._SCREEN_SIZE[1] / size)
            for y in range(height + 2):
                for x in range(width + 2):
                    self._screen.blit(
                        pg.transform.scale(
                            self._textures[data['texture']], (size, size),
                        ),
                        self._gen_screen_pos(origin + (x * scale, y * scale)),
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
                key = gen_tile_key(tile)
                data = self._tilemap.get(key)
                self._draw_tile(self._gen_screen_pos(tile), data)

    def _draw_tool(self: Self, tile: Point) -> None:
        pos = self._gen_screen_pos(tile)
        if self._tool == 'place':
            self._draw_tile(pos, self._data, 128)
            return None
        rect = (pos, (self._zoom, self._zoom))
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
            key = gen_tile_key(tile)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_z:
                        self._zoom += 8
                    elif event.key == pg.K_x:
                        self._zoom = max(self._zoom - 4, 8)
                    elif event.key == pg.K_MINUS:
                        dictionary = (
                            self._tilemap['bg'] if event.mod & pg.KMOD_SHIFT
                            else self._data
                        )
                        if dictionary is not self._data: # yes i know is sloppy
                            self._unsaved = 1
                        dictionary['texture'] = (
                            (dictionary['texture'] - 1) % len(self._textures)
                        )
                    elif event.key == pg.K_EQUALS:
                        dictionary = (
                            self._tilemap['bg'] if event.mod & pg.KMOD_SHIFT
                            else self._data
                        )
                        if dictionary is not self._data:
                            self._unsaved = 1
                        dictionary['texture'] = (
                            (dictionary['texture'] + 1) % len(self._textures)
                        )
                    elif event.key == pg.K_LEFTBRACKET:
                        if event.mod & pg.KMOD_SHIFT:
                            scale = self._tilemap['bg']['scale']
                            self._tilemap['bg']['scale'] = max(scale - 1, 1)
                            self._unsaved = 1
                        else:
                            self._lines_dex = (
                                (self._lines_dex - 1) % len(self._lines)
                            )
                            self._data['lines'] = self._lines[self._lines_dex]
                    elif event.key == pg.K_RIGHTBRACKET:
                        if event.mod & pg.KMOD_SHIFT:
                            self._tilemap['bg']['scale'] += 1
                            self._unsaved = 1
                        else:
                            self._lines_dex = (
                                (self._lines_dex + 1) % len(self._lines)
                            )
                            self._data['lines'] = self._lines[self._lines_dex]
                    elif event.key == pg.K_9:
                        self._type_dex = (self._type_dex - 1) % len(self._types)
                    elif event.key == pg.K_0:
                        self._type_dex = (self._type_dex + 1) % len(self._types)
                    elif event.key == pg.K_b:
                        self._tool = 'place'
                    elif event.key == pg.K_e:
                        self._tool = 'remove'
                    elif event.key == pg.K_i:
                        self._tool = 'eyedropper'
                    elif event.mod & pg.KMOD_CTRL:
                        if event.key == pg.K_COMMA:
                            self._number = max(self._number - 1, 0)
                        elif event.key == pg.K_PERIOD:
                            self._number += 1
                        elif event.key == pg.K_s:
                            self._save(f'{self._number}.json')
                            self._unsaved = 0
                        elif event.key == pg.K_l:
                            self._load(f'{self._number}.json')

            # Update
            movement = (
                keys[pg.K_d] - keys[pg.K_a],
                keys[pg.K_s] - keys[pg.K_w],
            )
            speed = (
                (8 if keys[pg.K_LSHIFT] else 4)
                * (not keys[pg.K_LCTRL] and not keys[pg.K_RCTRL])
            )
            self._pos += (
                movement[0] / self._zoom * speed * rel_game_speed,
                movement[1] / self._zoom * speed * rel_game_speed,
            )
            if mouse[0]:
                if self._tool == 'place':
                    self._tilemap[key] = copy.deepcopy(self._data)
                    self._unsaved = 1
                elif self._tool == 'remove':
                    try:
                        self._tilemap.pop(key)
                        self._unsaved = 1
                    except KeyError:
                        pass
                elif self._tool == 'eyedropper':
                    try:
                        self._data = copy.deepcopy(self._tilemap[key])
                    except KeyError:
                        pass
            
            # Render
            self._change_title()
            self._draw_background()
            self._draw_grid()
            self._draw_tiles()
            self._draw_tool(tile)

            ## Info
            self._draw_tile(pg.Vector2(0, 0), self._data, size=32)

            text = self._font.render(
                f'number: {self._number}\n'
                '\n'
                f'key: {key}\n'
                f'texture: {self._data['texture']}\n'
                f'lines:\n{'\n'.join(str(item) for item in self._data['lines'])}\n'
                f'type: {self._data['type']}\n',
                1,
                (0, 255, 0),
            )
            self._screen.blit(text, (5, 32))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

