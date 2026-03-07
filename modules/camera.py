import math
from typing import Self
from numbers import Real

import pygame as pg
from pygame.typing import Point

from modules.utils import gen_tile_key
from modules.level import Level


class Camera(object):
    def __init__(self: Self,
                 level: Level,
                 pos: pg.Vector2,
                 zoom: int=16,
                 flatness: Real=36): # -1 for perfect flat
        self._level = level
        self._pos = pos
        self._zoom = zoom
        self._flatness = flatness

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

    @property
    def flatness(self: Self) -> Real:
        return self._flatness

    @flatness.setter
    def flatness(self: Self, value: Real) -> None:
        self._flatness = value

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
        mult = (1 - (1 - 0.025))**rel_game_speed
        self._pos += (follow - self._pos) * mult

    def _render_shadow(self: Self,
                       surf: pg.Surface,
                       texture: pg.Surface,
                       pos: pg.Vector2) -> None:
        shadow = pg.transform.hsl(texture, 0, 0, -0.9)
        shadow.set_alpha(128)
        surf.blit(shadow, (pos[0], pos[1] + 0.75 * texture.height))

    def render(self: Self, surf: pg.Surface) -> None:
        # Background
        surf.fill((0, 0, 0))
        data = self._level._tilemap['bg']
        if data['texture'] != -1:
            scale = data['scale']
            size = scale * self._zoom
            origin = pg.Vector2(
                (self._pos[0] - surf.width / 2 / self._zoom) // scale * scale,
                (self._pos[1] - surf.height / 2 / self._zoom) // scale * scale,
            )
            if self._flatness != -1:
                origin += (
                    self._pos[0] / self._flatness % scale,
                    self._pos[1] / self._flatness % scale,
                )
                # ^ subtle depth effect
            width = int(surf.width / size)
            height = int(surf.height / size)
            for y in range(-1, height + 2):
                for x in range(-1, width + 2):
                    surf.blit(
                        pg.transform.scale(
                            self._level._textures[data['texture']],
                            (size, size),
                        ),
                        self.gen_screen_pos(
                            origin + (x * scale, y * scale),
                            surf.size,
                        ),
                    )
        
        # Entities
        for entity in self._level._entities:
            texture = pg.transform.scale(
                entity._surf, [entity._render_width * self._zoom] * 2,
            )
            pos = self.gen_screen_pos(
                entity._pos - [entity._render_width / 2] * 2, surf.size,
            )
            self._render_shadow(surf, texture, pos)
            surf.blit(texture, pos)

        # Tiles
        origin = pg.Vector2(
            math.floor(self._pos[0] - surf.width / 2 / self._zoom),
            math.floor(self._pos[1] - surf.height / 2 / self._zoom),
        )
        width = int(surf.width / self._zoom)
        height = int(surf.height / self._zoom)
        
        # -1 for tile shadows
        for y in range(-1, height + 2):
            for x in range(-1, width + 2):
                tile = origin + (x, y)
                tile_key = gen_tile_key(tile)
                data = self._level._tilemap.get(tile_key)
                if data is not None:
                    texture = pg.transform.scale(
                        self._level._textures[data['texture']],
                        (self._zoom, self._zoom),
                    )
                    pos = self.gen_screen_pos(tile, surf.size)
                    self._render_shadow(surf, texture, pos)
                    surf.blit(texture, pos)
        
        # Particles
        for particle in self._level._particles:
            radius = particle._radius * self._zoom
            texture = pg.Surface([radius * 2] * 2)
            texture.set_colorkey((0, 0, 0))
            texture.set_alpha(particle._alpha)
            pg.draw.circle(
                texture,
                particle._color,
                [radius] * 2,
                radius,
            )
            pos = self.gen_screen_pos(
                particle._pos - [particle._radius] * 2, surf.size,
            )
            surf.blit(texture, pos)


