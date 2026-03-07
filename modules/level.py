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
        
        # Particles
        dead = set()
        for particle in self._particles:
            particle.update(rel_game_speed)
            if particle.dead:
                dead.add(particle)
        for particle in dead:
            self._particles.remove(particle)


