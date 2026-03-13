import time
import math
import random
from typing import Self
from typing import Optional
from typing import Callable
from numbers import Real

import pygame as pg
from pygame import mixer as mx
from pygame.typing import Point

from modules.utils import SMALL
from modules.utils import load_fnt
from modules.utils import load_img
from modules.utils import load_sfx
from modules.utils import load_mus
from modules.utils import load_tilemap
from modules.utils import gen_text_surf
from modules.utils import gen_text_button_surf
from modules.level import Entity
from modules.level import Puck
from modules.level import Boost
from modules.level import Damage
from modules.level import Function
from modules.level import Level
from modules.camera import Camera
from modules.menu import Widget
from modules.menu import Text
from modules.menu import Button
from modules.menu import Menu


# Sloppy coded but it's okay because it's a game jam
# scattered functions, hardcoded values, etc.
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
            flags=self._SCREEN_FLAGS, # flags don't really work in pygbag
            vsync=self._settings['vsync'], # not sure about vsync in pygbag
        )
        pg.display.set_caption('Icebox')
        self._surface = pg.Surface(self._SURF_SIZE)
        self._running = 0
        self._level_timer = 0
    
        self._state = 'tutorial' # alive, tutorial, dead, win, finish
        self._restarted = 1 # so first click (tutorial) doesn't count
        self._strokes = 0
        self._bounces = 0
        self._par_beaten = 0 # for current level
        self._star_gotten = 0 # for current level
        self._star_won = 0
        self._total_strokes = 0
        self._total_bounces = 0
        self._pars_beaten = 0
        self._stars = 0
        
        # Assets
        self._font = pg.font.SysFont('Arial', int(self._SURF_SIZE[1] / 15))
        # using alpha in images instead of colorkey for shadow
        self._images = {
            'logo': load_img('logo.png', alpha=1),
            'launch': {
                'can': load_img('launch', 'can.png', alpha=1),
                'cant': load_img('launch', 'cant.png', alpha=1),
            },
            'puck': (
                load_img('puck', '1.png', alpha=1),
                load_img('puck', '2.png', alpha=1),
                load_img('puck', '3.png', alpha=1),
                load_img('puck', '4.png', alpha=1),
                load_img('puck', '5.png', alpha=1),
                load_img('puck', '6.png', alpha=1),
                load_img('puck', '7.png', alpha=1),
                load_img('puck', '8.png', alpha=1),
                load_img('puck', '9.png', alpha=1),
                load_img('puck', '10.png', alpha=1),
                load_img('puck', 'dead.png', alpha=1),
            ),
            'finish': load_img('backgrounds', 'finish.png'),
            'textures': (
                load_img('backgrounds', 'main.png'),
                load_img('obstacles', 'square.png'),
                load_img('obstacles', 'triangle1.png', alpha=1),
                load_img('obstacles', 'triangle2.png', alpha=1),
                load_img('obstacles', 'triangle3.png', alpha=1),
                load_img('obstacles', 'triangle4.png', alpha=1),
                load_img('specials', 'boost_up.png'),
                load_img('specials', 'boost_down.png'),
                load_img('specials', 'boost_left.png'),
                load_img('specials', 'boost_right.png'),
                load_img('specials', 'damage_10.png', alpha=1),
                load_img('specials', 'win.png'),
                load_img('specials', 'trophy.png', alpha=1),
                load_img('specials', 'star.png', alpha=1),
                load_img('specials', 'star_empty.png', alpha=1),
            )
        }
        pg.mixer.set_num_channels(64) # so shatter sound can play
        self._sounds = {
            'bounce': load_sfx('bounce.mp3'),
            'die': load_sfx('die.mp3'),
            'stroke': load_sfx('stroke.mp3'),
            'boost': load_sfx('boost.mp3'),
            'damage': load_sfx('damage.mp3'),
            'star': load_sfx('star.mp3'),
            'start': load_sfx('start.mp3'),
            'win': load_sfx('win.mp3'),
            'finish': load_sfx('finish.mp3'),
        }
        
        # Game Stuff
        ## Data
        # health and par amounts for each level
        # Also used to determine number of levels
        self._health = (10, 12, 9, 18, 24, 22, 31, 22, 100, )
        self._par = (2, 3, 1, 2, 1, 1, 2, 2, 1, )
        self._specials = {
            'boost_up': Boost('up', sound=self._sounds['boost']),
            'boost_down': Boost('down', sound=self._sounds['boost']),
            'boost_left': Boost('left', sound=self._sounds['boost']),
            'boost_right': Boost('right', sound=self._sounds['boost']),
            'damage': Damage(5, sound=self._sounds['damage']),
            'win': Function(self._win, one_for_all=1),
            'star': Function(self._star),
        }
        # REMINDME: MAKESURE TO SET LEVEL DEX TO ZERO BEFORE SUBMITTING
        self._level_dex = 8
        self._puck = Puck(
            surfs=self._images['puck'][:-1],
            width=0.9,
            render_width=1,
            health=self._health[self._level_dex],
        )
        self._level = Level(
            entities={self._puck},
            tilemap=load_tilemap(self._level_dex),
            specials=self._specials,
            textures=self._images['textures'],
        )
        self._camera = Camera(self._level, (0, 4), zoom=16)
        
        # Menus
        self._init_menus()
        self._transition_timer = 0

    def _init_menus(self: Self) -> None:
        self._widgets = {
            'tutorial': {
                # 'arrow' is added below
                'restart': Text(
                    self._font,
                    f'R to restart',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.325),
                ),
                'stroke': Text(
                    self._font,
                    f'Stroke is -5',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.45),
                ),
                'bounce': Text(
                    self._font,
                    f'Bounce is -1',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.575),
                ),
            },
            'dead': {
                'strokes': Text(
                    self._font,
                    f'Strokes: {self._strokes}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.325),
                ),
                'bounces': Text(
                    self._font,
                    f'Bounces: {self._bounces}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.45),
                ),
            },
            'win': {
                'strokes': Text(
                    self._font,
                    f'Strokes: {self._strokes}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.325),
                ),
                'bounces': Text(
                    self._font,
                    f'Bounces: {self._bounces}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.45),
                ),
                'spare': Text(
                    self._font,
                    f'Spare: {self._puck.health}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.575),
                ),
            },
            'finish': {
                'strokes': Text(
                    self._font,
                    f'Total strokes: {self._total_strokes}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.275),
                ),
                'bounces': Text(
                    self._font,
                    f'Total bounces: {self._total_bounces}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.4),
                ),
                'pars': Text(
                    self._font,
                    f'Pars beaten: {self._pars_beaten}',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.525),
                ),
                'stars': Text(
                    self._font,
                    f'Stars: {self._stars} / 3',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.65),
                ),
            },
        }
        # Arrow for tutorial
        tutorial_arrow = pg.Surface(self._SURF_SIZE)
        tutorial_arrow.set_colorkey((0, 0, 0))
        end_pos = self._font.size(str(self._puck.health)) + pg.Vector2(12, 12)
        start_pos = pg.Vector2(
            self._widgets['tutorial']['restart'].rect.left,
            self._SURF_SIZE[1] / 2,
        )
        vector = end_pos - start_pos
        points = [
            pg.Vector2(point).rotate(vector.angle) * 16 + end_pos
            for point in ((0, 0.25), (0, -0.25), (0.5, 0))
        ]
        pg.draw.line( # Shadow
            tutorial_arrow,
            (96, 0, 0),
            start_pos + (0, 2),
            end_pos + (0, 2),
            2,
        )
        pg.draw.polygon( # Shadow of triangle
            tutorial_arrow,
            (96, 0, 0),
            [point + (0, 2) for point in points],
        )
        pg.draw.line( # Line
            tutorial_arrow,
            (255, 0, 0),
            start_pos,
            end_pos,
            2,
        )
        # Triangle
        pg.draw.polygon(tutorial_arrow, (255, 0, 0), points)
        self._widgets['tutorial']['arrow'] = Widget(
            tutorial_arrow, pg.Vector2(self._SURF_SIZE) / 2,
        )

        self._menus = {
            'tutorial': Menu({
                Widget(
                    self._images['logo'],
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.2)
                ),
                self._widgets['tutorial']['arrow'],
                self._widgets['tutorial']['restart'],
                self._widgets['tutorial']['stroke'],
                self._widgets['tutorial']['bounce'],
                Button(
                    gen_text_button_surf(self._font, 'Start'),
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.75),
                    self._start,
                ),
            }),
            'dead': Menu({
                Text(
                    self._font,
                    'YOU SHATTERED!',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.2),
                ),
                self._widgets['dead']['strokes'],
                self._widgets['dead']['bounces'],
                Button(
                    gen_text_button_surf(self._font, 'Restart'),
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.75),
                    self._restart,
                ),
            }),
            'win': Menu({
                Text(
                    self._font,
                    'YOU BEAT THE LEVEL!',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.2),
                ),
                self._widgets['win']['strokes'],
                self._widgets['win']['bounces'],
                self._widgets['win']['spare'],
                Button(
                    gen_text_button_surf(self._font, 'Next Level'),
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.75),
                    self._next_level,
                ),
            }),
            'finish': Menu({
                Text(
                    self._font,
                    'YOU FINISHED!',
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.15),
                ),
                self._widgets['finish']['strokes'],
                self._widgets['finish']['bounces'],
                self._widgets['finish']['pars'],
                self._widgets['finish']['stars'],
                Button(
                    gen_text_button_surf(self._font, 'Play Again'),
                    (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] * 0.825),
                    self._play_again,
                ),
            })
        }

    def _play_again(self: Self) -> None:
        self._level_dex = 0
        self._total_bounces = 0
        self._total_strokes = 0
        self._pars_beaten = 0
        self._stars = 0
        self._star_won = 0
        self._restart()

    def _randomize_camera_pos(self: Self) -> None:
        self._camera.pos = (
            random.random() * 10 - 5,
            random.random() * 10 - 5,
        )

    def _start(self: Self) -> None:
        self._restart(self._camera.pos)

    def _restart(self: Self, camera_pos: Optional[pg.Vector2]=None) -> None:
        self._state = 'alive'
        self._strokes = 0
        self._bounces = 0
        self._star_gotten = 0
        self._restarted = 1
        # par_beaten and star_gotten aren't reset here so that if one resets 
        # during a win it still counts

        self._puck.health = self._health[self._level_dex]
        self._puck.max_health = self._health[self._level_dex]
        self._puck.pos = (0, 0)
        self._puck.velocity = (0, 0)
        self._puck.boost = (0, 0)
        self._level.clear_particles()
        self._level.tilemap = load_tilemap(self._level_dex)
        if camera_pos is None:
            self._randomize_camera_pos()
        else:
            self._camera_pos = camera_pos
        if self._star_won:
            for key in self._level.tiles(self._specials['star']):
                self._star(self._puck, self._level.tilemap[key])

        self._sounds['start'].play()

    def _next_level(self: Self) -> None:
        if self._level_dex > len(self._par) - 2:
            self._transition_timer = 0
            self._state = 'finish'
            self._widgets['finish']['strokes'].text = f'Total strokes: {self._total_strokes}'
            self._widgets['finish']['bounces'].text = f'Total bounces: {self._total_bounces}'
            self._widgets['finish']['pars'].text = f'Pars beaten: {self._pars_beaten}'
            self._widgets['finish']['stars'].text = f'Stars: {self._stars} / 3'
            if self._stars >= 3:
                self._widgets['finish']['stars'].color = (0, 255, 0)
            self._sounds['finish'].play()
        else:
            self._level_dex += 1
            self._star_won = 0
            self._par_beaten = 0
            self._restart()

    def _darken_surf(self: Self) -> None:
        # pg.transform.hsl gives weird results
        surf = pg.Surface(self._SURF_SIZE)
        surf.set_alpha(96)
        self._surface.blit(surf, (0, 0))

    def _render_menu_bg(self: Self, bg: Optional[pg.Surface]=None) -> None:
        if bg is None:
            bg = self._level.background
        if bg is not None:
            size = self._camera.zoom * self._level.tilemap['bg']['scale']
            bg = pg.transform.scale(bg, (size, size))
            offset = pg.Vector2(
                self._level_timer / 240 % 1 * size,
                self._level_timer / 240 % 1 * size
            )
            for y in range(-1, int(self._SURF_SIZE[1] / bg.height) + 1):
                for x in range(-1, int(self._SURF_SIZE[0] / bg.width) + 1):
                    self._surface.blit(bg, (x * size, y * size) + offset)
            self._darken_surf()

    def _star(self: Self, entity: Entity, data: dict) -> None:
        data['texture'] = 14 # empty start texture
        self._star_gotten = 1
        if not self._star_won:
            self._sounds['star'].play()

    def _win(self: Self, entity: Entity, data: dict) -> None:
        self._transition_timer = 0
        self._state = 'win'
        self._widgets['win']['strokes'].text = (
            f'Strokes: {self._strokes}'
        )
        self._widgets['win']['bounces'].text = (
            f'Bounces: {self._bounces}'
        )
        self._widgets['win']['spare'].text = (
            f'Spare: {self._puck.health} '
            f'(Par: {self._par[self._level_dex]})'
        )
        if self._puck.health == 0:
            self._widgets['win']['spare'].color = (0, 255, 255)
        elif self._puck.health > self._par[self._level_dex]:
            self._widgets['win']['spare'].color = (0, 255, 0)
            if not self._par_beaten:
                self._pars_beaten += 1
                self._par_beaten = 1
        elif self._puck.health == self._par[self._level_dex]:
            self._widgets['win']['spare'].color = (255, 255, 0)
        else:
            self._widgets['win']['spare'].color = (255, 255, 255)
        if self._star_gotten and not self._star_won:
            self._stars += 1
            self._star_won = 1
        self._sounds['win'].play()

    def _end_dead(self: Self) -> None:
        self._puck.autosurf = 0
        self._puck.surf = self._images['puck'][10]

    def _spawn_particle_at_puck(self: Self) -> None:
        velocity = (
            -self._puck.net_velocity
            .rotate(random.random() * 20 - 10)
            * random.random()
        )
        self._level.spawn_particle(
            color=(255, 255, 255),
            radius=0.1,
            pos=self._puck.pos,
            velocity=velocity,
        )

    def _render_transition(self: Self, timer: Real, time: Real) -> None:
        if 0 <= timer <= time:
            surf = pg.Surface(self._SURF_SIZE)
            surf.set_colorkey((255, 255, 255))
            pg.draw.circle(
                surf,
                (255, 255, 255),
                (self._SURF_SIZE[0] / 2, self._SURF_SIZE[1] / 2),
                abs(pg.math.smoothstep(-0.5, 0.5, timer / time))
                * pg.Vector2(self._SURF_SIZE).magnitude() + 2,
            )
            self._surface.blit(surf, (0, 0))

    def _render_hud(self: Self, can_launch: bool) -> None:
        surf = gen_text_surf(self._font, str(self._puck.health))
        # tutorial needs offset and surf dimensions so placed here
        self._surface.blit(surf, (4, 4))
        if can_launch: # Launch Indicator
            surf = pg.transform.scale(
                self._images['launch']['can'], (32, 32),
            )
            self._surface.blit(
                surf,
                (self._SURF_SIZE[0] - 4 - surf.width, 4),
            )
        else:
            surf = pg.transform.scale(
                self._images['launch']['cant'], (32, 32),
            )
            self._surface.blit(
                surf,
                (self._SURF_SIZE[0] - 4 - surf.width, 4),
            )

    def _end(self: Self,
             rel_game_speed: Real,
             mouse_pos: Point,
             mouse_pressed: tuple[bool],
             key: str,
             func: Callable=lambda: 1) -> None:
        self._transition_timer += rel_game_speed
        if self._puck.net_speed > SMALL:
            self._transition_timer = 0
            self._level.update(rel_game_speed)
            self._puck.velocity *= 0.9**rel_game_speed
            func()
            self._camera.update(rel_game_speed, self._puck.pos)
            self._camera.render(self._surface)
        elif self._transition_timer >= 30:
            self._menus[key].update(
                rel_game_speed, mouse_pos, mouse_pressed,
            )
            self._render_menu_bg()
            self._menus[key].render(self._surface)
        else:
            self._camera.update(rel_game_speed, self._puck.pos)
            self._camera.render(self._surface)
        self._render_transition(self._transition_timer, 60)

    def _finish(self: Self,
                rel_game_speed: Real,
                mouse_pos: Point,
                mouse_pressed: tuple[bool]) -> None:
        self._transition_timer += rel_game_speed
        if self._transition_timer < 30:
            self._menus['win'].update(
                rel_game_speed, mouse_pos, mouse_pressed,
            )
            self._render_menu_bg()
            self._menus['win'].render(self._surface)
        else:
            self._menus['finish'].update(
                rel_game_speed, mouse_pos, mouse_pressed,
            )
            self._render_menu_bg(self._images['finish'])
            self._menus['finish'].render(self._surface)
        self._render_transition(self._transition_timer, 60)

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        while self._running:
            # Delta time
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED
            self._level_timer += rel_game_speed

            mouse = pg.mouse.get_pressed()
            mouse_pos = pg.mouse.get_pos()
            # scale down mouse pos
            mouse_pos = (mouse_pos[0] / self._SURF_RATIO[0],
                         mouse_pos[1] / self._SURF_RATIO[1])
            # using center instead of player pos so that vector doesn't 
            # move when camera moves
            vector = pg.Vector2(
                self._SURF_SIZE[0] / 2 - mouse_pos[0],
                self._SURF_SIZE[1] / 2 - mouse_pos[1],
            ) / self._camera.zoom
            # cant scale zero vector
            if vector.magnitude() > 5:
                vector.scale_to_length(5)
            can_launch = self._puck.speed < SMALL

            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:
                        self._restart()
                elif event.type in ( # will mess up delta time
                    pg.WINDOWRESIZED,
                    pg.WINDOWMINIMIZED,
                    pg.WINDOWMAXIMIZED,
                    pg.WINDOWFOCUSGAINED,
                    pg.WINDOWFOCUSLOST,
                ):
                    start_time = time.time()
                    delta_time = 0
                    rel_game_speed = 0
                elif self._state in ('tutorial', 'dead', 'win', 'finish'):
                    self._menus[self._state].handle_event(event)
                else:
                    if event.type == pg.MOUSEBUTTONDOWN:
                        self._restarted = 0
                    elif (event.type == pg.MOUSEBUTTONUP
                        and can_launch
                        and not self._restarted):
                        self._strokes += 1
                        self._total_strokes += 1
                        self._puck.health -= 5
                        self._puck.velocity = (
                            vector * 0.1 if vector else pg.Vector2(0, 0)
                        )
                        sound = self._sounds['stroke']
                        sound.set_volume(vector.magnitude())
                        sound.play()
            
            if self._state == 'tutorial':
                self._level.update(rel_game_speed)
                # self._camera.update(rel_game_speed, self._puck.pos)
                self._camera.render(self._surface)
                self._darken_surf()
                self._menus['tutorial'].update(
                    rel_game_speed, mouse_pos, mouse,
                )
                self._menus['tutorial'].render(self._surface)
                self._render_hud(can_launch)
            elif self._state == 'dead':
                self._end(
                    rel_game_speed,
                    mouse_pos,
                    mouse,
                    'dead',
                    self._end_dead,
                )
            elif self._state == 'win':
                self._end(
                    rel_game_speed,
                    mouse_pos,
                    mouse,
                    'win',
                    self._spawn_particle_at_puck,
                )
            elif self._state == 'finish':
                self._finish(rel_game_speed, mouse_pos, mouse)
            else:
                self._puck.autosurf = 1
                # Update
                self._level.update(rel_game_speed)
                self._camera.update(rel_game_speed, self._puck.pos)

                if self._puck.bounced:
                    self._bounces += 1
                    self._total_bounces += 1
                    sound = self._sounds['bounce']
                    sound.set_volume(self._puck.net_speed * 0.8)
                    sound.play()

                if self._puck.dead:
                    self._transition_timer = 0
                    self._state = 'dead'
                    self._widgets['dead']['strokes'].text = (
                        f'Strokes: {self._strokes}'
                    )
                    self._widgets['dead']['bounces'].text = (
                        f'Bounces: {self._bounces}'
                    )
                    self._sounds['die'].play()

                # Render 
                self._camera.render(self._surface)
                if mouse[0] and can_launch and not self._restarted:
                    start_pos = self._camera.gen_screen_pos(
                        self._puck.pos, self._surface.size,
                    )
                    end_pos = start_pos - vector * self._camera.zoom
                    points = [ # Triangle arrow
                        pg.Vector2(point).rotate(vector.angle)
                        * self._camera.zoom
                        + start_pos
                        for point in ((0, 0.25), (0, -0.25), (0.5, 0))
                    ]
                    pg.draw.line( # Shadow of line
                        self._surface,
                        (0, 96, 0),
                        start_pos + (0, 2),
                        end_pos + (0, 2),
                        2,
                    )
                    pg.draw.polygon( # Shadow of triangle
                        self._surface,
                        (0, 96, 0),
                        [point + (0, 2) for point in points],
                    )
                    pg.draw.line( # Line
                        self._surface,
                        (0, 255, 0),
                        start_pos,
                        end_pos,
                        2,
                    )
                    # Triangle
                    pg.draw.polygon(self._surface, (0, 255, 0), points)
                self._render_hud(can_launch)
                    
            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

