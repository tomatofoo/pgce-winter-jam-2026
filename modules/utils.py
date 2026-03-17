import os
import math
import json
from typing import Optional
from numbers import Real

import pygame as pg
from pygame import mixer as mx
from pygame.typing import Point
from pygame.typing import ColorLike


SMALL = 0.01

def load_fnt(*args: str, size: int=20) -> None:
    fnt = pg.font.Font(os.path.join('data', 'fonts', *args), size)
    return fnt

def load_img(*args: str, size: Point=None, alpha: bool=0) -> pg.Surface:
    img = pg.image.load(os.path.join('data', 'images', *args))
    img = img.convert_alpha() if alpha else img.convert()
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

def get_line_x(line: tuple[Point], y: Real, do_clamp: bool=True) -> Optional[Real]:
    point0 = line[0]
    point1 = line[1]
    try:
        return pg.math.lerp(
            point0[0], point1[0],
            pg.math.invlerp(point0[1], point1[1], y),
            do_clamp,
        )
    except ValueError:
        return None

def get_line_y(line: tuple[Point], x: Real, do_clamp: bool=True) -> Optional[Real]:
    point0 = line[0]
    point1 = line[1]
    try: 
        return pg.math.lerp(
            point0[1], point1[1],
            pg.math.invlerp(point0[0], point1[0], x),
            do_clamp,
        )
    except ValueError:
        return None

def dist_ptols(pos: pg.Vector2, line: tuple[pg.Vector2, pg.Vector2]) -> Real:
    # vector projection formula but get t parameter instead of point
    # clamp parameter between 0 and 1
    # then get distance to the point that the parameter is at
    # https://stackoverflow.com/a/1501725/24845999

    # line[0] is only guaranteed pg.Vector2
    line = (pg.Vector2(line[0]), line[1])
    difference = line[1] - line[0]
    if not difference:
        # pos.distance_to(line[0])
        return line[0].distance_to(pos)

    t = pg.math.clamp(
        difference.dot(pos - line[0]) / difference.magnitude_squared(),
        0, 1,
    )
    # return pos.distance_to(line[0] + t * difference)
    return (line[0] + t * difference).distance_to(pos)

def dist_rtols(rect: pg.Rect,
               line: tuple[pg.Vector2, pg.Vector2],
               clipline_test: bool=1) -> Real:
    if clipline_test and rect.clipline(line):
        return 0
    return min(
        dist_ptols(rect.topleft, line),
        dist_ptols(rect.bottomleft, line),
        dist_ptols(rect.topright, line),
        dist_ptols(rect.bottomright, line),
        dist_ptols(line[0], (rect.topleft, rect.topright)),
        dist_ptols(line[0], (rect.topright, rect.bottomright)),
        dist_ptols(line[0], (rect.bottomright, rect.bottomleft)),
        dist_ptols(line[0], (rect.bottomleft, rect.topleft)),
        dist_ptols(line[1], (rect.topleft, rect.topright)),
        dist_ptols(line[1], (rect.topright, rect.bottomright)),
        dist_ptols(line[1], (rect.bottomright, rect.bottomleft)),
        dist_ptols(line[1], (rect.bottomleft, rect.topleft)),
    )

def gen_text_surf(font: pg.Font,
                  text: str,
                  color: ColorLike=(255, 255, 255),
                  dropshadow: bool=1) -> pg.Surface:
    size = font.size(text)
    surf = pg.Surface((size[0], size[1] + 2))
    surf.set_colorkey((0, 0, 0))
    if dropshadow:
        shadow_color = (color[0] * 0.2, color[1] * 0.2, color[2] * 0.2)
        surf.blit(font.render(text, 0, shadow_color), (0, 2))
    surf.blit(font.render(text, 0, color), (0, 0))
    return surf

def gen_text_button_surf(font: pg.Font,
                         text: str,
                         txcolor: ColorLike=(255, 255, 255),
                         bgcolor: ColorLike=(255, 0, 0),
                         olcolor: ColorLike=(255, 255, 255),
                         olwidth: int=2,
                         padding: int=8,
                         dropshadow: bool=1) -> pg.Surface:

    size = font.size(text)
    offset = 2 * dropshadow
    surf = pg.Surface((
        size[0] + padding * 2 + offset,
        size[1] + padding * 2 + offset,
    ))
    surf.fill(bgcolor)
    pg.draw.rect(surf, olcolor, (0, 0, surf.width, surf.height), olwidth)
    surf.blit(
        gen_text_surf(font, text, txcolor, dropshadow), (padding, padding),
    )

    return surf

