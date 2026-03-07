from __future__ import annotations

import os
import time
import math
import json
import random
from typing import Self
from numbers import Real

import pygame as pg
from pygame import mixer as mx
from pygame.typing import Point
from pygame.typing import ColorLike


SMALL = 0.01

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


class Particle(object):
    def __init__(self: Self,
                 color: ColorLike, # color cannot be 000000 (colorkey)
                 radius: Real=0.5,
                 lifetime: Real=60,
                 pos: pg.Vector2=pg.Vector2(0, 0),
                 velocity: pg.Vector2=pg.Vector2(1, 1)) -> None:

        self._color = pg.Color(color)
        self._alpha = 255
        self._radius = radius
        self._pos = pg.Vector2(pos)
        self._velocity = pg.Vector2(velocity)
        self._lifetime = lifetime
        self._timer = lifetime

    @property
    def color(self: Self) -> pg.Color:
        return self._color

    @color.setter
    def color(self: Self, value: ColorLike) -> None:
        self._color = pg.Color(value)

    @property
    def alpha(self: Self) -> Real:
        return self._alpha

    @property
    def radius(self: Self) -> pg.Color:
        return self._color

    @color.setter
    def radius(self: Self, value: ColorLike) -> None:
        self._color = pg.Color(value)

    @property
    def velocity(self: Self) -> pg.Vector2:
        return self.velocity.copy()

    @velocity.setter
    def velocity(self: Self, value: pg.Vector2) -> None:
        self._velocity = pg.Vector2(value)

    @property
    def dead(self: Self) -> bool:
        return self._timer <= 0

    def update(self: Self, rel_game_speed: Real) -> None:
        self._alpha = pg.math.lerp(0, 255, self._timer / self._lifetime)
        self._timer -= rel_game_speed
        self._velocity *= 0.999**rel_game_speed
        self._pos += self._velocity
        

class Level(object):
    def __init__(self: Self,
                 entities: set[Entity],
                 tilemap: dict,
                 textures: tuple[pg.Surface]):
        self._entities = set()
        self.entities = entities
        self._particles = set()
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

    @property
    def particles(self: Self) -> set[Particle]:
        return self._particles

    def spawn_particle(self: Self,
                       color: ColorLike,
                       radius: Real=0.5,
                       lifetime: Real=60,
                       pos: pg.Vector2=pg.Vector2(0, 0),
                       velocity: pg.Vector2=pg.Vector2(1, 1)) -> None:
        self._particles.add(Particle(
            color=color,
            radius=radius,
            lifetime=lifetime,
            pos=pos,
            velocity=velocity,
        ))

    def update(self: Self, rel_game_speed: Real) -> None:
        # Entities
        for entity in self._entities:
            entity.update(rel_game_speed)
        
        # Particles
        dead = set()
        for particle in self._particles:
            particle.update(rel_game_speed)
            if particle.dead:
                dead.add(particle)
        for particle in dead:
            self._particles.remove(particle)


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
                 render_width: Optional[Real]=None,
                 health: int=100):
        
        self._level = None
        self._surf = surf
        self._pos = pg.Vector2(pos)
        self._width = width
        self.render_width = render_width
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
    def render_width(self: Self) -> Real:
        return self._render_width

    @render_width.setter
    def render_width(self: Self, value: Optional[Real]) -> None:
        if value is None:
            value = self._width
        self._render_width = value

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

    @property
    def speed(self: Self) -> Real:
        return self._velocity.magnitude()

    @speed.setter
    def speed(self: Self, value: Real) -> None:
        self._velocity.scale_to_length(value)

    @property
    def dead(self: Self) -> bool:
        return self._health <= 0
    
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
                    ) - 1
                elif self._velocity[0] < 0:
                    entity_rect.left = max(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) + 1
                self._pos[0] = entity_rect.centerx / scale
        
        self._pos[1] += self._velocity[1] * rel_game_speed
        entity_rect = self.rect(scale)
        for line in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if self._velocity[1] > 0:
                    entity_rect.bottom = min(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    ) - 1
                elif self._velocity[1] < 0:
                    entity_rect.top = max(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    ) + 1
                self._pos[1] = entity_rect.centery / scale


class Puck(Entity):
    def __init__(self: Self,
                 surfs: tuple[pg.Surface],
                 pos: Point=(0, 0),
                 width: Real=1,
                 render_width: Optional[Real]=None,
                 health: int=100,
                 bounce_sound: Optional[mx.Sound]=None,
                 die_sound: Optional[mx.Sound]=None):

        super().__init__(
            surf=surfs[0],
            pos=pos,
            width=width,
            render_width=render_width,
        )
        self._surfs = surfs
        self._surf_dex = 0
        self._health = health
        self._max_health = health

        self._sounds = {
            'bounce': bounce_sound,
            'die': die_sound,
        }

    @property
    def surfs(self: Self) -> tuple[pg.Surface]:
        return self._surfs
    
    @surfs.setter
    def surfs(self: Self, value: tuple[pg.Surface]) -> None:
        self._surfs = value

    @property
    def bounce_sound(self: Self) -> Optional[mx.Sound]:
        return self._sounds['bounce']

    @bounce_sound.setter
    def bounce_sound(self: Self, value: Optional[mx.Sound]) -> None:
        self._sounds['bounce'] = value

    @property
    def die_sound(self: Self) -> Optional[mx.Sound]:
        return self._sounds['die']

    @die_sound.setter
    def die_sound(self: Self, value: Optional[mx.Sound]) -> None:
        self._sounds['die'] = value

    def _bounce(self: Self,
                line: tuple[Point],
                initial_angle: Real=None) -> None:
        if initial_angle is None:
            initial_angle = self._velocity.angle
        # Bounce across line
        difference = line[1][0] - line[0][0]
        angle = math.degrees(math.atan2(
            (line[1][1] - line[0][1]), difference,
        )) if difference else 90
        self._velocity.rotate_ip(
            angle + angle - initial_angle - self._velocity.angle
        )
        
    def update(self: Self, rel_game_speed: Real) -> None:
        scale = 100
        initial = self._velocity.copy()
        bounced = 0

        self._pos[0] += initial[0] * rel_game_speed
        entity_rect = self.rect(scale)
        for line in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                # The +1 is scaled down by scale (100)
                # It accounts for inaccuracies
                # Also btw collisions mgiht be messed up
                # Yes I know it isn't pretty but its a game jam
                if initial[0] > 0:
                    entity_rect.right = min(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) - 1
                    bounced = 1
                elif initial[0] < 0:
                    entity_rect.left = max(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) + 1
                    bounced = 1

                # angle would be same so don't need to scale down line
                self._bounce(line, initial.angle)
                self._pos[0] = entity_rect.centerx / scale
                self._health = max(self._health - 1, 0)
        
        self._pos[1] += initial[1] * rel_game_speed
        entity_rect = self.rect(scale)
        for line in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if initial[1] > 0:
                    entity_rect.bottom = min(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    ) - 1
                    bounced = 1
                elif initial[1] < 0:
                    entity_rect.top = max(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right), 
                    ) + 1
                    bounced = 1

                self._bounce(line, initial.angle)
                self._pos[1] = entity_rect.centery / scale
                self._health = max(self._health - 1, 0)

        if self._velocity.magnitude() > SMALL:
            self._velocity *= 0.98**rel_game_speed
        else:
            self._velocity.update(0, 0)
        
        if self.dead:
            sound = self._sounds['die']
            if self._surf_dex < len(self._surfs) and sound is not None:
                sound.play()
                self._surf_dex = len(self._surfs)
        else:
            surf_dex = int(math.floor(
                (1 - (self._health / self._max_health)) * len(self._surfs)
            ))
            self._surf = self._surfs[surf_dex]

        # Sounds
        sound = self._sounds['bounce']
        if bounced and sound is not None:
            sound.set_volume(self._velocity.magnitude() * 0.8)
            sound.play()


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
            if vector.magnitude() > 5:
                vector.scale_to_length(5)
            can_launch = self._puck.speed < SMALL
            
            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.MOUSEBUTTONUP and can_launch:
                    self._puck.velocity = (
                        vector * 0.1 if vector else pg.Vector2(0, 0)
                    )
                    sound = self._sounds['launch']
                    sound.set_volume(vector.magnitude())
                    sound.play()

            self._level.update(rel_game_speed)
            self._camera.update(rel_game_speed, self._puck.pos)

            # Render 
            self._surface.fill((0, 0, 0))
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

