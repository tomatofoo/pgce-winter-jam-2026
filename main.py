import time
from typing import Self
from numbers import Real

import pygame as pg
from pygame.typing import Point


def gen_tile_key(obj: Point):
    return f'{int(math.floor(obj[0]))};{int(math.floor(obj[1]))}'

def get_line_x(line: tuple[Point], y: Real) -> Real:
    point0 = pg.Vector2(line[0])
    point1 = pg.Vector2(line[1])
    t = (y - point0[1]) / (point1[1] - point0[1])
    return pg.math.lerp(point0[0], point1[0], t)

def get_line_y(line: tuple[Point], x: Real) -> Real:
    point0 = pg.Vector2(line[0])
    point1 = pg.Vector2(line[1])
    t = (x - point0[0]) / (point1[0] - point0[0])
    return pg.math.lerp(point0[1], point1[1], t)


class Level(object):
    def __init__(self: Self, tilemap: dict, textures: tuple[pg.Surface]):
        self._tilemap = tilemap
        self._textures = textures

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

    def render(self: Self, pos: pg.Vector2) -> None:
        pass


class Entity(object):

    _TILE_OFFSETS = (
        (-1, -1), (0, -1), (1, -1),
        (-1,  0), (0,  0), (1,  0),
        (-1,  1), (0,  1), (1,  1),
    )

    def __init__(self: Self,
                 level: Level,
                 pos: Point=(0, 0),
                 width: Real=0.75):

        self._level = level
        self._pos = pg.Vector2(pos)
        self._velocity = pg.Vector2(0, 0)
        self._width = width

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
    def velocity(self: Self) -> pg.Vector2:
        return self._velocity.copy()

    @velocity.setter
    def velocity(self: Self, value: Point) -> None:
        self._velocity = pg.Vector2(value)
    
    @property
    def rect(self: Self) -> pg.FRect:
        rect = pg.FRect(0, 0, self._width, self._width)
        rect.center = self._pos
        return rect

    def _get_lines_around(self: Self) -> None:
        lines = []
        for offset in self._TILE_OFFSETS:
            tile_key = gen_tile_key(self._pos + offset)
            data = self._level._map.get(tile_key)
            if data is not None:
                for line in data['lines']:
                    lines.append(lines)

    def update(self: Self, rel_game_speed: Real) -> None:
        self._pos[0] += self._velocity[0] * rel_game_speed
        entity_rect = self.rect
        for line in self._get_lines_around():
            if entity_rect.clipline(line):
                if self._velocity[0] > 0:
                    entity_rect.right = rect.left
                elif self._velocity[0] < 0:
                    entity_rect.left = rect.right
                self._pos[0] = entity_rect.centerx
        
        self._pos[1] += self._velocity[1] * rel_game_speed
        entity_rect = self.rect
        for line in self._get_lines_around():
            if entity_rect.clipline(line):
                if self._velocity[1] > 0:
                    entity_rect.bottom = rect.top
                elif self._velocity[1] < 0:
                    entity_rect.top = rect.bottom
                self._pos[1] = entity_rect.centery


    def render(self: Self) -> None:
        self._pos[0]


class Puck(Entity):
    def __init__(self: Self,
                 level: Level,
                 pos: Point=(0, 0),
                 width: Real=0.5,
                 health: int=50):
        super().__init__(
            level=level,
            pos=pos,
            width=width,
        )
        self._health = health

    @property
    def health(self: Self) -> int:
        return self._health

    @health.setter
    def health(self: Self, value: int) -> None:
        self._health = value

    def update(self: Self, rel_game_speed: Real) -> None:
        self._pos[0] += self._velocity[0] * rel_game_speed
        entity_rect = self.rect
        for lines in self._get_lines_around():
            if entity_rect.clipline(line):
                if self._velocity[0] > 0:
                    entity_rect.right = rect.left
                elif self._velocity[0] < 0:
                    entity_rect.left = rect.right
                self._pos[0] = entity_rect.centerx
        
        self._pos[1] += self._velocity[1] * rel_game_speed
        entity_rect = self.rect
        for line in self._get_lines_around():
            if entity_rect.clipline(line):
                if self._velocity[1] > 0:
                    entity_rect.bottom = rect.top
                elif self._velocity[1] < 0:
                    entity_rect.top = rect.bottom
                self._pos[1] = entity_rect.centery

    def render(self: Self) -> None:
        pass


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

        self._map = {}

        self._player = Entity(
        
        # Positions
        self._camera_pos = pg.Vector2(0, 0)
        self._pos = self._get_map_pos(
            (self._SCREEN_SIZE[0] / 2, self._SCREEN_SIZE[1] / 2),
        )
        self._puck_pos = pg.Vector2(0, 0)
        
        # Velocities
        self._velocity = pg.Vector2(0, 0)
        self._puck_velocity = pg.Vector2(0, 0)

        self._puck_rect = pg.Rect()

    def _get_map_pos(self: Self, screen_pos: Point) -> pg.Vector2:
        screen_pos - self._camera_pos

    def _get_screen_pos(self: Self, map_pos: Point) -> pg.Vector2:
        pass

    def _update(self: Self, rel_game_speed: Real) -> None:
        self._pos += self._velocity * rel_game_speed
        
        mult = (1 - (1 - 0.25))**rel_game_speed
        self._camera_pos += (self._pos - self._puck_pos) * mult

    def _render_map(self: Self) -> None:
        pass

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        while self._running:
            # Delta time
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED
            
            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.MOUSEBUTTONDOWN:
                    vector = event.pos - self._pos
                    self._velocity = (
                        vector.normalize() * 0.05 if vector
                        else pg.Vector2(0, 0)
                    )
            
            # Update
            self._update(rel_game_speed)
            
            # Render 
            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

