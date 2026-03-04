from __future__ import annotations

import os
import time
import math
from typing import Self
from numbers import Real

import pygame as pg
from pygame.typing import Point


SMALL = 0.00001

def load_img(*args: str, size: Point=None) -> pg.Surface:
    img = pg.image.load(os.path.join('data', 'images', *args))
    if size is not None:
        img = pg.transform.scale(img, size)
    return img

def gen_tile_key(obj: Point):
    return f'{int(math.floor(obj[0]))};{int(math.floor(obj[1]))}'

def get_line_x(line: tuple[Point], y: Real) -> Real:
    point0 = pg.Vector2(line[0])
    point1 = pg.Vector2(line[1])
    difference = point1[1] - point0[1]
    t = (y - point0[1]) / difference if difference else 0
    return pg.math.lerp(point0[0], point1[0], t, 0)

def get_line_y(line: tuple[Point], x: Real) -> Real:
    point0 = pg.Vector2(line[0])
    point1 = pg.Vector2(line[1])
    difference = point1[0] - point0[0]
    t = (x - point0[0]) / difference if difference else 0
    return pg.math.lerp(point0[1], point1[1], t, 0)


class Level(object):
    def __init__(self: Self,
                 entities: set[Entity],
                 tilemap: dict,
                 textures: tuple[pg.Surface]):
        self._entities = {}
        self.entities = entities
        self._tilemap = tilemap
        self._textures = textures

    @property
    def entities(self: Self) -> set[Entity]:
        return self._entities

    @entities.setter
    def entities(self: Self, value: set[Entity]) -> None:
        for entity in self._entities:
            entity._level = None
        self._entities = value
        for entity in value:
            entity._level = self

    @property
    def tilemap(self: Self) -> dict:
        return self._tilemap

    @tilemap.setter
    def tilemap(self: Self, value: dict) -> None:
        self._tilemap = value

    @property
    def textures(self: Self) -> tuple[pg.Surface]:
        return self._textures

    @textures.setter
    def textures(self: Self, value: tuple[pg.Surface]) -> None:
        self._textures = value

    def update(self: Self, rel_game_speed: Real) -> None:
        for entity in self._entities:
            entity.update(rel_game_speed)


class Entity(object):

    _TILE_OFFSETS = (
        (-1, -1), (0, -1), (1, -1),
        (-1,  0), (0,  0), (1,  0),
        (-1,  1), (0,  1), (1,  1),
    )

    def __init__(self: Self,
                 surf: pg.Surface,
                 pos: Point=(0, 0),
                 width: Real=1,
                 health: int=100):
        
        self._level = None
        self._surf = surf
        self._pos = pg.Vector2(pos)
        self._width = width
        self._velocity = pg.Vector2(0, 0)

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @surf.setter
    def surf(self: Self, value: pg.Surface) -> None:
        self._surf = value

    @property
    def x(self: Self) -> Real:
        return self._pos[0]

    @x.setter
    def x(self: Self, value: Real) -> None:
        self._pos[0] = value

    @property
    def y(self: Self) -> Real:
        return self._pos[1]

    @y.setter
    def y(self: Self, value: Real) -> None:
        self._pos[1] = value

    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos.copy()

    @pos.setter
    def pos(self: Self, value: Point) -> None:
        self._pos = pg.Vector2(value)

    @property
    def width(self: Self) -> Real:
        return self._width

    @width.setter
    def width(self: Self, value: Real) -> None:
        self._width = value

    @property
    def velocity(self: Self) -> pg.Vector2:
        return self._velocity.copy()

    @property
    def health(self: Self) -> int:
        return self._health

    @health.setter
    def health(self: Self, value: int) -> None:
        self._health = value

    @property
    def velocity(self: Self) -> pg.Vector2:
        return self._velocity.copy()

    @velocity.setter
    def velocity(self: Self, value: Point) -> None:
        self._velocity = pg.Vector2(value)
    
    def rect(self: Self, scale: Real=1) -> pg.FRect:
        rect = pg.FRect(0, 0, self._width * scale, self._width * scale)
        rect.center = self._pos * scale
        return rect

    def _get_lines_around(self: Self, scale: Real=1) -> list[tuple[Point]]:
        lines = []
        for offset in self._TILE_OFFSETS:
            tile = pg.Vector2(
                math.floor(self._pos[0] + offset[0]),
                math.floor(self._pos[1] + offset[1]),
            )
            tile_key = gen_tile_key(tile)
            data = self._level._tilemap.get(tile_key)
            if data is not None:
                for line in data['lines']:
                    lines.append(
                        ((tile + line[0]) * scale, (tile + line[1]) * scale),
                    )
        return lines

    def update(self: Self, rel_game_speed: Real) -> None:
        scale = 100

        self._pos[0] += self._velocity[0] * rel_game_speed
        entity_rect = self.rect(scale)
        for line in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if self._velocity[0] > 0:
                    entity_rect.right = min(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    )
                elif self._velocity[0] < 0:
                    entity_rect.left = max(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    )
                self._pos[0] = entity_rect.centerx / scale
        
        self._pos[1] += self._velocity[1] * rel_game_speed
        entity_rect = self.rect(scale)
        for line in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if self._velocity[1] > 0:
                    entity_rect.bottom = min(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    )
                elif self._velocity[1] < 0:
                    entity_rect.top = max(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    )
                self._pos[1] = entity_rect.centery / scale


class Puck(Entity):
    def __init__(self: Self,
                 surfs: tuple[pg.Surface],
                 pos: Point=(0, 0),
                 width: Real=1,
                 health: int=50):

        super().__init__(
            surf=surfs[0],
            pos=pos,
            width=width,
        )
        self._surfs = surfs
        self._health = health
        self._max_health = health

    @property
    def surfs(self: Self) -> tuple[pg.Surface]:
        return self._surfs
    
    @surfs.setter
    def surfs(self: Self, value: tuple[pg.Surface]) -> None:
        self._surfs = value

    @property
    def health(self: Self) -> int:
        return self._health

    @health.setter
    def health(self: Self, value: int) -> None:
        self._health = value

    def bounce(self: Self, line: tuple[Point]) -> None:
        pass

    def update(self: Self, rel_game_speed: Real) -> None:
        scale = 100

        self._pos[0] += self._velocity[0] * rel_game_speed
        entity_rect = self.rect(scale)
        for line in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if self._velocity[0] > 0:
                    entity_rect.right = min(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) - SMALL * scale
                elif self._velocity[0] < 0:
                    entity_rect.left = max(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) + SMALL * scale
                
                self._pos[0] = entity_rect.centerx / scale
                self._health = max(self._health - 1, 0)
        
        self._pos[1] += self._velocity[1] * rel_game_speed
        entity_rect = self.rect(scale)
        for line in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if self._velocity[1] > 0:
                    entity_rect.bottom = min(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    ) - SMALL * scale
                elif self._velocity[1] < 0:
                    entity_rect.top = max(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right), 
                    ) + SMALL * scale

                self._pos[1] = entity_rect.centery / scale
                self._health = max(self._health - 1, 0)

        if self._velocity.magnitude() > SMALL:
            self._velocity *= 0.9**rel_game_speed
        else:
            self._velocity.update(0, 0)
        
        if self._health:
            self._surf = self._surfs[math.floor(
                (1 - (self._health / self._max_health)) * len(self._surfs)
            )]


class Camera(object):
    def __init__(self: Self, level: Level, pos: pg.Vector2, zoom: int=16):
        self._level = level
        self._pos = pos
        self._zoom = zoom

    @property
    def level(self: Self) -> Level:
        return self._level

    @level.setter
    def level(self: Self, value: Level) -> None:
        self._level = value

    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos

    @pos.setter
    def pos(self: Self, value: pg.Vector2) -> None:
        self._pos = value

    @property
    def zoom(self: Self) -> int:
        return self._zoom

    @zoom.setter
    def zoom(self: Self, value: int) -> None:
        self._zoom = value

    def gen_map_pos(self: Self,
                    screen_pos: Point,
                    surf_size: Point) -> pg.Vector2:
        return (
            (screen_pos - pg.Vector2(surf_size) / 2)
            / self._zoom
            + self._pos
        )

    def gen_screen_pos(self: Self,
                       map_pos: Point,
                       surf_size: Point) -> pg.Vector2:
        return (
            (map_pos - self._pos) * self._zoom
            + (surf_size[0] / 2, surf_size[1] / 2)
        )

    def update(self: Self, rel_game_speed: Real, follow: pg.Vector2) -> None:
        mult = (1 - (1 - 0.01))**rel_game_speed
        self._pos += (follow - self._pos) * mult

    def render(self: Self, surf: pg.Surface) -> None:
        origin = pg.Vector2(
            math.floor(self._pos[0] - surf.width / 2 / self._zoom),
            math.floor(self._pos[1] - surf.height / 2 / self._zoom),
        )
        width = int(surf.width / self._zoom)
        height = int(surf.height / self._zoom)

        for y in range(height):
            for x in range(width):
                tile = origin + (x, y)
                tile_key = gen_tile_key(tile)
                data = self._level._tilemap.get(tile_key)
                if data is not None:
                    texture = pg.transform.scale(
                        self._level._textures[data['texture']],
                        (self._zoom, self._zoom),
                    )
                    surf.blit(texture, self.gen_screen_pos(tile, surf.size))

        for entity in self._level._entities:
            texture = pg.transform.scale(
                entity._surf, [entity._width * self._zoom] * 2,
            )
            pos = self.gen_screen_pos(
                entity._pos - [entity._width / 2] * 2, surf.size,
            )
            surf.blit(texture, pos)


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
        
        self._puck = Puck((load_img('player.png'),),)
        self._level = Level(
            entities={self._puck},
            tilemap={
                '0;0': {
                    'texture': 0,
                    'lines': (
                        ((0, 0), (1, 0)),
                        ((1, 0), (1, 1)),
                        ((1, 1), (0, 1)),
                        ((0, 1), (0, 0)),
                    ),
                }
            },
            textures=(
                load_img('obstacle.png'),
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

            mouse_pos = pg.mouse.get_pos()
            vector = self._camera.gen_map_pos(
                (mouse_pos[0] / self._SURF_RATIO[0],
                 mouse_pos[1] / self._SURF_RATIO[1]),
                self._surface.size,
            ) - self._puck.pos
            vector = vector.normalize() if vector else pg.Vector2(0, 0)
            
            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self._puck.velocity = vector * 0.2

            self._level.update(rel_game_speed)
            self._camera.update(rel_game_speed, self._puck.pos)

            # Render 
            self._surface.fill((0, 0, 0))
            self._camera.render(self._surface)
            puck_pos = self._camera.gen_screen_pos(
                self._puck.pos, self._surface.size,
            )
            pg.draw.line(
                self._surface,
                (0, 255, 0),
                puck_pos,
                puck_pos + vector * self._camera.zoom * 2,
                2,
            )
            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

