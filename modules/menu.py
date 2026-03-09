from typing import Self
from typing import Callable
from numbers import Real

import pygame as pg
from pygame.typing import Point

from modules.utils import gen_text_surf


# POS IS CENTER POS
class Widget(object):
    def __init__(self: Self, surf: pg.Surface, pos: Point) -> None:
        self._surf = surf
        self._rect = pg.Rect(0, 0, surf.width, surf.height)
        self._rect.center = pos
        self._pos = pos

    @property
    def surf(self: Self) -> None:
        return self._surf

    @property
    def pos(self: Self) -> None:
        return self._pos

    @property
    def rect(self: Self) -> pg.Rect:
        return self._rect

    def handle_event(self: Self, event: pg.Event) -> None:
        pass
    
    def update(self: Self,
               rel_game_speed: Real,
               mouse_pos: Point,
               mouse_pressed: tuple[bool]) -> None:
        pass


class Text(Widget):
    def __init__(self: Self,
                 font: pg.Font,
                 text: str,
                 pos: Point,
                 dropshadow: bool=1) -> None:
        self._font = font
        self._dropshadow = dropshadow
        self.text = text
        super().__init__(self._surf, pos)

    @property
    def font(self: Self) -> pg.Font:
        return self._font

    @font.setter
    def font(self: Self, value: pg.Font) -> None:
        self._font = value

    @property
    def text(self: Self) -> str:
        return self._text

    @text.setter
    def text(self: Self, value: str) -> None:
        self._text = value
        self._surf = gen_text_surf(self._font, self._text, self._dropshadow)

    @property
    def dropshadow(self: Self) -> bool:
        return self._dropshadow

    @dropshadow.setter
    def dropshadow(self: Self, value: bool) -> None:
        self._dropshadow = value
        self.text = self._text


class Button(Widget):
    def __init__(self: Self,
                 surf: pg.Surface,
                 pos: Point,
                 func: Callable=lambda: 1) -> None:
        super().__init__(surf, pos)
        self._original_surf = surf.copy()
        self._func = func

    @property
    def func(self: Self) -> Callable:
        return self._func

    @func.setter
    def func(self: Self, value: Callable) -> None:
        self._func = value

    def handle_event(self: Self, event: pg.Event, scale: Point=(2, 2)) -> None:
        if (event.type == pg.MOUSEBUTTONDOWN
            and self._rect.collidepoint(
                (event.pos[0] / scale[0], event.pos[1] / scale[1]),
            )
            and event.button == 1):
            self._func()

    def update(self: Self,
               rel_game_speed: Real,
               mouse_pos: Point,
               mouse_pressed: tuple[bool]) -> None:
        if self._rect.collidepoint(mouse_pos):
            if mouse_pressed[0]:
                self._surf = pg.transform.hsl(self._original_surf, 0, 0, -0.5)
            else:
                self._surf = pg.transform.hsl(self._original_surf, 0, 0, 0.5)
        else:
            self._surf = self._original_surf


class Menu(object):
    def __init__(self: Self, widgets: set[Widget]) -> None:
        self._widgets = widgets

    @property
    def widgets(self: Self) -> set[Widget]:
        return self._widgets

    @widgets.setter
    def widgets(self: Self, value: set[Widget]) -> None:
        self._widgets = value

    def handle_event(self: Self, event: pg.Event) -> None:
        for widget in self._widgets:
            widget.handle_event(event)

    def update(self: Self,
               rel_game_speed: Real,
               mouse_pos: Point,
               mouse_pressed: tuple[bool]) -> None:
        for widget in self._widgets:
            widget.update(rel_game_speed, mouse_pos, mouse_pressed)

    def render(self: Self, surf: pg.Surface) -> None:
        for widget in self._widgets:
            widget_surf = widget.surf
            rect = widget_surf.get_rect()
            rect.center = widget.pos
            surf.blit(widget_surf, rect.topleft)

