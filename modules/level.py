from __future__ import annotations

import math
from typing import Self
from numbers import Real

import pygame as pg
from pygame import mixer as mx
from pygame.typing import Point
from pygame.typing import ColorLike

from modules.utils import SMALL
from modules.utils import gen_tile_key
from modules.utils import get_line_x
from modules.utils import get_line_y


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
        self._boost = pg.Vector2(0, 0)

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
        self._health = max(value, 0)

    @property
    def velocity(self: Self) -> pg.Vector2:
        return self._velocity.copy()

    @velocity.setter
    def velocity(self: Self, value: pg.Vector2) -> None:
        self._velocity = pg.Vector2(value)

    @property
    def boost(self: Self) -> pg.Vector2:
        return self._boost.copy()

    @boost.setter
    def boost(self: Self, value: pg.Vector2) -> None:
        self._boost = pg.Vector2(value)

    @property
    def speed(self: Self) -> Real:
        return self._velocity.magnitude()

    @speed.setter
    def speed(self: Self, value: Real) -> None:
        self._velocity.scale_to_length(value)

    @property
    def boost_speed(self: Self) -> Real:
        return self._boost.magnitude()

    @boost_speed.setter
    def boost_speed(self: Self, value: Real) -> None:
        self._boost.scale_to_length(value)

    @property
    def net_velocity(self: Self) -> None:
        return self._velocity + self._boost

    @property
    def net_speed(self: Self) -> Real:
        return self.net_velocity.magnitude()

    @property
    def dead(self: Self) -> bool:
        return self._health <= 0
    
    def rect(self: Self, scale: Real=1) -> pg.FRect:
        rect = pg.FRect(0, 0, self._width * scale, self._width * scale)
        rect.center = self._pos * scale
        return rect

    def _get_lines_around(self: Self,
                          scale: Real=1) -> list[Special, tuple[Point], dict]:
        lines = []
        for offset in self._TILE_OFFSETS:
            tile = pg.Vector2(
                math.floor(self._pos[0] + offset[0]),
                math.floor(self._pos[1] + offset[1]),
            )
            tile_key = gen_tile_key(tile)
            data = self._level._tilemap.get(tile_key)
            if data is not None:
                special = None
                special_type = data['type']
                if special_type != 'normal':
                    special = self._level._special_key[special_type]
                for line in data['lines']:
                    lines.append((
                        special,
                        ((tile + line[0]) * scale, (tile + line[1]) * scale),
                        data,
                    ))
        return lines

    def _get_special_rects_around(
        self: Self,
        pos: pg.Vector2
    ) -> list[tuple[Special, pg.Rect, dict]]:
        rects = []
        for offset in self._TILE_OFFSETS:
            tile = pg.Vector2(
                math.floor(self._pos[0] + offset[0]),
                math.floor(self._pos[1] + offset[1]),
            )
            tile_key = gen_tile_key(tile)
            data = self._level._tilemap.get(tile_key)
            if data is not None and data['type'] != 'normal':
                special = self._level._special_key[data['type']]
                if not special._bounce:
                    rects.append((special, pg.Rect(tile, (1, 1)), data))
        return rects

    def update(self: Self, rel_game_speed: Real) -> None:
        scale = 100
        velocity = self._velocity + self._boost

        pos = self._pos + velocity * rel_game_speed
        entity_rect = pg.FRect(0, 0, self._width, self._width)
        entity_rect.center = pos
        for special, rect, data in self._get_special_rects_around(pos):
            if entity_rect.colliderect(rect):
                special.interact(self, data)

        bounced = (None, None) # special, data

        self._pos[0] += velocity[0] * rel_game_speed
        entity_rect = self.rect(scale)
        for special, line, data in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if velocity[0] > 0:
                    entity_rect.right = min(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) - 1
                    bounced = (special, data)
                elif velocity[0] < 0:
                    entity_rect.left = max(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) + 1
                    bounced = (special, data)
                self._pos[0] = entity_rect.centerx / scale
        
        self._pos[1] += velocity[1] * rel_game_speed
        entity_rect = self.rect(scale)
        for special, line, data in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if velocity[1] > 0:
                    entity_rect.bottom = min(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    ) - 1
                    bounced = (special, data)
                elif velocity[1] < 0:
                    entity_rect.top = max(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    ) + 1
                    bounced = (special, data)
                self._pos[1] = entity_rect.centery / scale

        if bounced[0] is not None:
            bounced[0].interact(self, bounced[1])
        
        if self._boost.magnitude() > SMALL:
            self._boost *= 0.95**rel_game_speed
        else:  
            self._boost.update(0, 0)


class Puck(Entity):
    def __init__(self: Self,
                 surfs: tuple[pg.Surface],
                 pos: Point=(0, 0),
                 width: Real=1,
                 render_width: Optional[Real]=None,
                 health: int=100):

        super().__init__(
            surf=surfs[0],
            pos=pos,
            width=width,
            render_width=render_width,
        )
        self._surfs = surfs
        self._health = health
        self._max_health = health
        self._bounced = 0

    @property
    def surfs(self: Self) -> tuple[pg.Surface]:
        return self._surfs
    
    @surfs.setter
    def surfs(self: Self, value: tuple[pg.Surface]) -> None:
        self._surfs = value

    @property
    def bounced(self: Self) -> bool: # if bounced in last update
        return self._bounced

    def _bounce(self: Self,
                line: tuple[Point],
                initial_angle: Real,
                vector: pg.Vector2) -> None:
        # Bounce across line
        difference = line[1][0] - line[0][0]
        angle = math.degrees(math.atan2(
            (line[1][1] - line[0][1]), difference,
        )) if difference else 90
        vector.rotate_ip(angle + angle - initial_angle - vector.angle)
        
    def update(self: Self, rel_game_speed: Real) -> None:
        scale = 100
        initial_velocity = self._velocity.copy()
        initial_boost = self._boost.copy()
        velocity = self._velocity + self._boost
        self._bounced = 0

        pos = self._pos + velocity * rel_game_speed
        entity_rect = pg.FRect(0, 0, self._width, self._width)
        entity_rect.center = pos
        for special, rect, data in self._get_special_rects_around(pos):
            if entity_rect.colliderect(rect):
                special.interact(self, data)

        bounced = (None, None) # special, data

        self._pos[0] += velocity[0] * rel_game_speed
        entity_rect = self.rect(scale)
        for special, line, data in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                # The +1 is scaled down by scale (100)
                # It accounts for inaccuracies
                # Also btw collisions mgiht be messed up
                # Yes I know it isn't pretty but its a game jam
                if velocity[0] > 0:
                    entity_rect.right = min(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) - 1
                    self._bounced = 1
                    bounced = (special, data)
                elif velocity[0] < 0:
                    entity_rect.left = max(
                        get_line_x(line, entity_rect.top),
                        get_line_x(line, entity_rect.bottom),
                    ) + 1
                    self._bounced = 1
                    bounced = (special, data)

                # angle would be same so don't need to scale down line
                self._bounce(line, initial_velocity.angle, self._velocity)
                self._bounce(line, initial_boost.angle, self._boost)
                self._pos[0] = entity_rect.centerx / scale
        
        self._pos[1] += velocity[1] * rel_game_speed
        entity_rect = self.rect(scale)
        for special, line, data in self._get_lines_around(scale):
            if entity_rect.clipline(line):
                if velocity[1] > 0:
                    entity_rect.bottom = min(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right),
                    ) - 1
                    self._bounced = 1
                    bounced = (special, data)
                elif velocity[1] < 0:
                    entity_rect.top = max(
                        get_line_y(line, entity_rect.left),
                        get_line_y(line, entity_rect.right), 
                    ) + 1
                    self._bounced = 1
                    bounced = (special, data)

                self._bounce(line, initial_velocity.angle, self._velocity)
                self._bounce(line, initial_boost.angle, self._boost)
                self._pos[1] = entity_rect.centery / scale

        if bounced[0] is not None:
            bounced[0].interact(self, bounced[1])

        self._health = max(self._health - self._bounced, 0)

        if self._velocity.magnitude() > SMALL:
            self._velocity *= 0.98**rel_game_speed
        else:
            self._velocity.update(0, 0)

        if self._boost.magnitude() > SMALL:
            self._boost *= 0.95**rel_game_speed
        else:  
            self._boost.update(0, 0)
        
        if not self.dead:
            surf_dex = int(math.floor(
                (1 - (self._health / self._max_health)) * len(self._surfs)
            ))
            self._surf = self._surfs[surf_dex]


class Special(object): # must be deepcopied per level
    def __init__(self: Self, bounce: bool=0) -> None:
        self._tiles = {} # tiles and data
        self._bounce = bounce

    @property
    def bounce(self: Self) -> bool:
        return self._bounce

    @bounce.setter
    def bounce(self: Self, value: bool) -> None:
        self._bounce = value

    def interact(self: Self, entity: Entity, data: dict) -> None:
        pass
    
    def _start_frame(self: Self) -> None: # called every frame by level.update
        pass

    def _end_frame(self: Self) -> None:
        pass

    def update(self: Self, rel_game_speed: Real, data: dict) -> dict:
        return data


class Boost(Special):
    # up, down, left, right are possible direction
    def __init__(self: Self,
                 angle: Real | str='up',
                 magnitude: Real=0.4,
                 sound: Optional[mx.Sound]=None,
                 bounce: bool=0) -> None:
        super().__init__(bounce)
        self.angle = angle
        self._magnitude = magnitude
        self._sound = sound
        self._boosts = [] # boosts in last frame
        # ^ used for sounds to not repeat
        # ^ not set because dict is unhashable
        self._last_boosts = self._boosts

    @property
    def angle(self: Self) -> Real:
        return self._angle

    @angle.setter
    def angle(self: Self, value: Real | str) -> None:
        if value == 'up':
            value = 90
        elif value == 'down':
            value = -90
        elif value == 'left':
            value = 180
        elif value == 'right':
            value = 0
        self._angle = value

    @property
    def magnitude(self: Self) -> Real:
        return self._magnitude

    @magnitude.setter
    def magnitude(self: Self, value: Real) -> None:
        self._magnitude = value

    @property
    def sound(self: Self) -> Optional[mx.Sound]:
        return self._sound

    @sound.setter
    def sound(self: Self, value: Optional[mx.Sound]) -> None:
        self._sound = value

    def interact(self: Self, entity: Entity, data: dict) -> None:
        boost = (entity, data)
        self._boosts.append(boost)

        entity.boost = pg.Vector2(self._magnitude, 0).rotate(self._angle)
        
        if self._sound is not None and boost not in self._last_boosts:
            self._sound.set_volume(self._magnitude)
            self._sound.play()

    def _end_frame(self: Self) -> None:
        self._last_boosts = self._boosts
        self._boosts = []


class End(Special):
    def __init__(self: Self, bounce: bool=0) -> None:
        super().__init__(bounce)
        self._touched = None

    @property
    def touched(self: Self) -> Optional[Entity]:
        return self._touched

    def interact(self: Self, entity: Entity, data: dict) -> None:
        self._touched = entity


class Level(object):
    def __init__(self: Self,
                 entities: set[Entity],
                 tilemap: dict,
                 specials: dict[str, Special]={},
                 textures: tuple[pg.Surface]=[pg.Surface((1, 1))]):
        self._entities = set()
        self.entities = entities
        self._particles = set()
        self._tilemap = tilemap
        self.specials = specials
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
        self.specials = self._special_key

    @property
    def specials(self: Self) -> dict[str, Special]:
        return self._special_key

    @specials.setter
    def specials(self: Self, value: dict[str, Special]) -> None:
        self._special_key = value
        self._specials = {}
        for key, value in self._tilemap.items():
            if key == 'bg':
                continue
            special_type = value['type']
            if special_type != 'normal':
                special = self._special_key[special_type]
                keys = self._specials.get(special)
                if keys is None:
                    self._specials[special] = []
                    keys = self._specials[special]
                keys.append(key)

    @property
    def textures(self: Self) -> tuple[pg.Surface]:
        return self._textures

    @textures.setter
    def textures(self: Self, value: tuple[pg.Surface]) -> None:
        self._textures = value

    @property
    def particles(self: Self) -> set[Particle]:
        return self._particles

    @property
    def background(self: Self) -> Optional[pg.Surface]:
        dex = self._tilemap['bg']['texture']
        return self._textures[dex] if dex != -1 else None

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

        # Specials
        for special, keys in self._specials.items():
            special._start_frame()
            for key in keys:
                self._tilemap[key] = special.update(
                    rel_game_speed, self._tilemap[key],
                )
            special._end_frame()
        
        # Particles
        dead = set()
        for particle in self._particles:
            particle.update(rel_game_speed)
            if particle.dead:
                dead.add(particle)
        for particle in dead:
            self._particles.remove(particle)


