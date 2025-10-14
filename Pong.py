#!/usr/bin/env python3
# Based on https://python101.readthedocs.io/pl/latest/pygame/pong/#
import pygame
from typing import Type
import skfuzzy as fuzz
import skfuzzy.control as fuzzcontrol

FPS = 30


class Board:
    def __init__(self, width: int, height: int):
        self.surface = pygame.display.set_mode((width, height), 0, 32)
        pygame.display.set_caption("AIFundamentals - PongGame")

    def draw(self, *args):
        background = (0, 0, 0)
        self.surface.fill(background)
        for drawable in args:
            drawable.draw_on(self.surface)

        pygame.display.update()


class Drawable:
    def __init__(self, x: int, y: int, width: int, height: int, color=(255, 255, 255)):
        self.width = width
        self.height = height
        self.color = color
        self.surface = pygame.Surface(
            [width, height], pygame.SRCALPHA, 32
        ).convert_alpha()
        self.rect = self.surface.get_rect(x=x, y=y)

    def draw_on(self, surface):
        surface.blit(self.surface, self.rect)


class Ball(Drawable):
    def __init__(
        self,
        x: int,
        y: int,
        radius: int = 20,
        color=(255, 10, 0),
        speed: int = 3,
    ):
        super(Ball, self).__init__(x, y, radius, radius, color)
        pygame.draw.ellipse(self.surface, self.color, [0, 0, self.width, self.height])
        self.x_speed = speed
        self.y_speed = speed
        self.start_speed = speed
        self.start_x = x
        self.start_y = y
        self.start_color = color
        self.last_collision = 0

    def bounce_y(self):
        self.y_speed *= -1

    def bounce_x(self):
        self.x_speed *= -1

    def bounce_y_power(self):
        self.color = (
            self.color[0],
            self.color[1] + 10 if self.color[1] < 255 else self.color[1],
            self.color[2],
        )
        pygame.draw.ellipse(self.surface, self.color, [0, 0, self.width, self.height])
        self.x_speed *= 1.1
        self.y_speed *= 1.1
        self.bounce_y()

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.x_speed = self.start_speed
        self.y_speed = self.start_speed
        self.color = self.start_color
        self.bounce_y()

    def move(self, board: Board, *args):
        self.rect.x += round(self.x_speed)
        self.rect.y += round(self.y_speed)

        if self.rect.x < 0 or self.rect.x > (
            board.surface.get_width() - self.rect.width
        ):
            self.bounce_x()

        if self.rect.y < 0 or self.rect.y > (
            board.surface.get_height() - self.rect.height
        ):
            self.reset()

        timestamp = pygame.time.get_ticks()
        if timestamp - self.last_collision < FPS * 4:
            return

        for racket in args:
            if self.rect.colliderect(racket.rect):
                self.last_collision = pygame.time.get_ticks()
                if (self.rect.right < racket.rect.left + racket.rect.width // 4) or (
                    self.rect.left > racket.rect.right - racket.rect.width // 4
                ):
                    self.bounce_y_power()
                else:
                    self.bounce_y()


class Racket(Drawable):
    def __init__(
        self,
        x: int,
        y: int,
        width: int = 80,
        height: int = 20,
        color=(255, 255, 255),
        max_speed: int = 10,
    ):
        super(Racket, self).__init__(x, y, width, height, color)
        self.max_speed = max_speed
        self.surface.fill(color)

    def move(self, x: int, board: Board):
        delta = x - self.rect.x
        delta = self.max_speed if delta > self.max_speed else delta
        delta = -self.max_speed if delta < -self.max_speed else delta
        delta = 0 if (self.rect.x + delta) < 0 else delta
        delta = (
            0
            if (self.rect.x + self.width + delta) > board.surface.get_width()
            else delta
        )
        self.rect.x += delta


class Player:
    def __init__(self, racket: Racket, ball: Ball, board: Board) -> None:
        self.ball = ball
        self.racket = racket
        self.board = board

    def move(self, x: int):
        self.racket.move(x, self.board)

    def move_manual(self, x: int):
        """
        Do nothing, control is defined in derived classes
        """
        pass

    def act(self, x_diff: int, y_diff: int):
        """
        Do nothing, control is defined in derived classes
        """
        pass


class PongGame:
    def __init__(
        self, width: int, height: int, player1: Type[Player], player2: Type[Player]
    ):
        pygame.init()
        self.board = Board(width, height)
        self.fps_clock = pygame.time.Clock()
        self.ball = Ball(width // 2, height // 2)

        self.opponent_paddle = Racket(x=width // 2, y=0)
        self.oponent = player1(self.opponent_paddle, self.ball, self.board)

        self.player_paddle = Racket(x=width // 2, y=height - 20)
        self.player = player2(self.player_paddle, self.ball, self.board)

    def run(self):
        while not self.handle_events():
            self.ball.move(self.board, self.player_paddle, self.opponent_paddle)
            self.board.draw(
                self.ball,
                self.player_paddle,
                self.opponent_paddle,
            )
            self.oponent.act(
                self.oponent.racket.rect.centerx - self.ball.rect.centerx,
                self.oponent.racket.rect.centery - self.ball.rect.centery,
            )
            self.player.act(
                self.player.racket.rect.centerx - self.ball.rect.centerx,
                self.player.racket.rect.centery - self.ball.rect.centery,
            )
            self.fps_clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT) or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                pygame.quit()
                return True
        keys = pygame.key.get_pressed()
        if keys[pygame.constants.K_LEFT]:
            self.player.move_manual(0)
        elif keys[pygame.constants.K_RIGHT]:
            self.player.move_manual(self.board.surface.get_width())
        return False


class NaiveOponent(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(NaiveOponent, self).__init__(racket, ball, board)

    def act(self, x_diff: int, y_diff: int):
        x_cent = self.ball.rect.centerx
        self.move(x_cent)


class HumanPlayer(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(HumanPlayer, self).__init__(racket, ball, board)

    def move_manual(self, x: int):
        self.move(x)


# ----------------------------------
# DO NOT MODIFY CODE ABOVE THIS LINE
# ----------------------------------

import numpy as np
import matplotlib.pyplot as plt


class FuzzyPlayer(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(FuzzyPlayer, self).__init__(racket, ball, board)

        self.W = float(self.board.surface.get_width())
        self.H = float(self.board.surface.get_height())
        self.VMAX = float(self.racket.max_speed)
        self.PW = float(self.racket.width)

        self.x_universe = np.linspace(-self.W/2, self.W/2, int(self.W) + 1)
        self.y_universe = np.linspace(0, self.H, int(self.H) + 1)

        span = self.W / 2.0

        self.x_mf = {
            "far_right": fuzz.trapmf(self.x_universe, [-span, -span, -0.22*span, -0.14*span]),
            "right":     fuzz.trimf( self.x_universe,  [-0.18*span, -0.09*span, -0.035*span]),
            "center":    fuzz.trimf( self.x_universe,  [ -0.05*span, 0.0, 0.05*span]),
            "left":      fuzz.trimf( self.x_universe,  [  0.035*span, 0.09*span, 0.18*span]),
            "far_left":  fuzz.trapmf(self.x_universe,  [  0.14*span, 0.22*span,  span,       span]),
        }

        self.y_mf = {
            "near": fuzz.trapmf(self.y_universe, [0, 0,            0.30*self.H, 0.55*self.H]),
            "mid":  fuzz.trimf( self.y_universe, [0.48*self.H,     0.68*self.H, 0.85*self.H]),
            "far":  fuzz.trapmf(self.y_universe, [0.78*self.H,     0.92*self.H, self.H,     self.H]),
        }

        V = self.VMAX
        self.velocity_fx = {
            "fast_left":   lambda xd, yd: -1.00 * V,
            "mid_left":    lambda xd, yd: -0.90 * V,
            "drift_left":  lambda xd, yd: -0.70 * V,

            "stop":        lambda xd, yd:  0.0,

            "drift_right": lambda xd, yd:  0.70 * V,
            "mid_right":   lambda xd, yd:  0.90 * V,
            "fast_right":  lambda xd, yd:  1.00 * V,
        }

        self.dead_x   = 1.2
        self.cutoff_v = 0.10
        self._prev_y_abs = None
        self._boost_gain = 1.10

    def _mf_x_map(self, x_val: float):
        return {n: fuzz.interp_membership(self.x_universe, mf, x_val)
                for n, mf in self.x_mf.items()}

    def _mf_y_map(self, y_abs: float):
        return {n: fuzz.interp_membership(self.y_universe, mf, y_abs)
                for n, mf in self.y_mf.items()}

    def _edge_shift(self, y_abs: float, x_val: float) -> float:
        y = self._mf_y_map(y_abs)
        w = 0.9*y["near"] + 0.4*y["mid"] + 0.05*y["far"]
        base = 0.25 * self.PW
        shift = w * base
        return np.copysign(shift, x_val)

    def _tsk_velocity(self, x_val: float, y_abs: float) -> float:
        x_edge = x_val - self._edge_shift(y_abs, x_val)

        x = self._mf_x_map(x_edge)
        y = self._mf_y_map(y_abs)
        f = self.velocity_fx

        rules = []

        rules.append( (x["far_left"],  f["fast_left"]) )
        rules.append( (x["far_right"], f["fast_right"]) )

        rules.append( (min(x["left"],  y["near"]),  f["fast_left"]) )
        rules.append( (min(x["right"], y["near"]),  f["fast_right"]) )

        rules.append( (min(x["left"],  y["mid"]),   f["mid_left"]) )
        rules.append( (min(x["right"], y["mid"]),   f["mid_right"]) )

        rules.append( (min(x["left"],  y["far"]),   f["drift_left"]) )
        rules.append( (min(x["right"], y["far"]),   f["drift_right"]) )

        rules.append( (x["center"], f["stop"]) )

        num = 0.0; den = 0.0
        for w_act, fx in rules:
            if w_act <= 0.0:
                continue
            z = fx(x_edge, y_abs)
            num += w_act * z
            den += w_act

        v = 0.0 if den <= 1e-9 else num/den
        if abs(v) < self.cutoff_v:
            v = 0.0
        return float(v)

    def act(self, x_diff: int, y_diff: int):
        x_val = float(x_diff)
        y_abs = float(abs(y_diff))

        if abs(x_val) < self.dead_x:
            v = 0.0
        else:
            v = self._tsk_velocity(x_val, y_abs)

        if self._prev_y_abs is not None and v != 0.0 and abs(x_val) >= self.dead_x:
            if y_abs < self._prev_y_abs - 0.001:
                v *= self._boost_gain
                v = max(-self.VMAX, min(self.VMAX, v))

        self._prev_y_abs = y_abs
        self.move(self.racket.rect.x + v)


if __name__ == "__main__":
    game = PongGame(800, 400, NaiveOponent, FuzzyPlayer)
    game.run()