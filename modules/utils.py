import os
import math
import json
from numbers import Real

import pygame as pg
from pygame import mixer as mx
from pygame.typing import Point
from pygame.typing import ColorLike


SMALL = 0.01

def load_fnt(*args: str, size: int=20) -> None:
    fnt = pg.font.Font(os.path.join('data', 'fonts', *args), size)
    return fnt

def load_img(*args: str, size: Point=None) -> pg.Surface:
    img = pg.image.load(os.path.join('data', 'images', *args))
    if size is not None:
        img = pg.transform.scale(img, size)
    return img

def load_sfx(*args: str) -> mx.Sound:
    sfx = mx.Sound(os.path.join('data', 'sounds', 'sfx', *args))
    return sfx

def load_mus(*args: str) -> mx.Sound:
    mus = mx.Sound(os.path.join('data', 'sounds', 'music', *args))
    return mus

def load_tilemap(number: int) -> dict:
    try:
        with open(os.path.join('data', 'maps', f'{number}.json'), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def gen_tile_key(obj: Point):
    return f'{int(math.floor(obj[0]))};{int(math.floor(obj[1]))}'

def get_line_x(line: tuple[Point], y: Real) -> Real:
    point0 = pg.Vector2(line[0])
    point1 = pg.Vector2(line[1])
    difference = point1[1] - point0[1]
    t = (y - point0[1]) / difference if difference else 0.5
    return pg.math.lerp(point0[0], point1[0], t)

def get_line_y(line: tuple[Point], x: Real) -> Real:
    point0 = pg.Vector2(line[0])
    point1 = pg.Vector2(line[1])
    difference = point1[0] - point0[0]
    t = (x - point0[0]) / difference if difference else 0.5
    return pg.math.lerp(point0[1], point1[1], t)

def gen_text_button_surf(font: pg.Font,
                         text: str,
                         bgcolor: ColorLike,
                         olcolor: ColorLike=(255, 255, 255),
                         olwidth: int=2,
                         padding: int=8,
                         dropshadow: bool=1) -> None:

    normal = font.render(text, 0, (255, 255, 255))
    offset = 2 * dropshadow
    surf = pg.Surface((
        normal.width + padding * 2 + offset,
        normal.height + padding * 2 + offset,
    ))
    surf.fill(bgcolor)
    pg.draw.rect(surf, olcolor, (0, 0, surf.width, surf.height), olwidth)
    if dropshadow:
        surf.blit(font.render(text, 0, (51, 51, 51)), (padding, padding + 2))
    surf.blit(normal, (padding, padding))

    return surf

