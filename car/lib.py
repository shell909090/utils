#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2022-12-27
@author: Shell.Xu
@copyright: 2022, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import math
import random
import turtle


def setup_world(lx, ly, ux, uy):
    lx -= 100
    ux += 100
    ly -= 100
    uy += 100
    turtle.setup(ux-lx, uy-ly)
    screen = turtle.getscreen()
    screen.setworldcoordinates(lx, ly, ux, uy)
    t = turtle.getturtle()
    t.ht()
    t.speed(0)
    return t


def sneaky(t, x, y):
    t.up()
    t.goto(x, y)
    t.down()


class Car(object):

    def __init__(self, screen, WB, RB, basepos=(0, 0)):
        self.screen = screen
        self.speed = 1
        self.fang = 0
        self.R = None
        self.Rs = [0, 0, 0, 0]
        self.WB = WB  # 轴距
        self.RB = RB/2  # 轮距

        self.ts = [turtle.RawTurtle(screen) for _ in range(4)]
        for i, color in enumerate(['red', 'crimson', 'blue', 'royalblue']):
            self.ts[i].pencolor(color)
            self.ts[i].speed(0)
        for i, pos in enumerate([(self.WB, self.RB), (self.WB, -self.RB), (0, self.RB), (0, -self.RB)]):
            pos = (sum(l) for l in zip(basepos, pos))
            sneaky(self.ts[i], *pos)

    def next(self, t):
        mv = self.speed*t
        if self.R is None:
            for tr in self.ts:
                tr.fd(mv)
        else:
            for tr, r in zip(self.ts, self.Rs):
                tr.circle(r, mv)

    def left(self, ang):
        if abs(self.fang+ang) > 35:
            raise Exception('front angle too big')
        self.fang += ang
        self.ts[0].setheading(self.ts[2].heading())
        self.ts[1].setheading(self.ts[3].heading())
        if self.fang == 0:
            self.R = None
            return
        self.R = self.WB/math.tan(math.pi*self.fang/180)
        self.Rs[0] = math.sqrt((self.R-self.RB)**2+self.WB**2)
        self.Rs[1] = math.sqrt((self.R+self.RB)**2+self.WB**2)
        self.Rs[2] = self.R-self.RB
        self.Rs[3] = self.R+self.RB
        if self.R < 0:
            self.Rs[0] = -self.Rs[0]
            self.Rs[1] = -self.Rs[1]
        self.ts[0].left(math.atan(self.WB/(self.R-self.RB))*180/math.pi)
        self.ts[1].left(math.atan(self.WB/(self.R+self.RB))*180/math.pi)

    def show_r(self):
        print(self.R, self.Rs)
        print(ang,
              math.atan(self.WB/(self.R-self.RB))*180/math.pi,
              math.atan(self.WB/(self.R+self.RB))*180/math.pi)

    def TR2SA(self, R):  # Turning radius to Steeing angle
        R0 = math.sqrt(R**2-self.WB**2)-self.RB
        return 180*math.atan(self.WB/R0)/math.pi

    def where_am_i(self):
        print(self.ts[0].xcor(), self.ts[0].ycor())
        print(self.ts[1].xcor(), self.ts[1].ycor())
        print(self.ts[2].xcor(), self.ts[2].ycor())
        print(self.ts[3].xcor(), self.ts[3].ycor())


class RandomCar(Car):

    def __init__(self, screen, WB, RB):
        pos = (10*random.random()-5, 10*random.random()-5)
        super(RandomCar, self).__init__(screen, WB, RB, pos)

    def next(self, t):
        x = 0.95 + 0.1*random.random()
        super(RandomCar, self).next(x*t)
