#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2022-12-27
@author: Shell.Xu
@copyright: 2022, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from lib import *


# https://www.3rxing.org/question/406fd8802f107614183.html
def ground_ZJZW():  # 直角转弯
    t = setup_world(0, -100, 700, 700)
    sneaky(t, 0, 230)
    t.fd(350)
    t.left(90)
    t.fd(350)
    t.right(90)
    sneaky(t, 0, -120)  # 30 to right
    t.fd(700)
    t.left(90)
    t.fd(700)


def ZJZW(car):
    # x = 385.6-230 = 155.6
    # 296.6 - sqrt(y**2 + x**2), to left
    # y + 350 - 546 = y - 196 = 296.6 - sqrt(y**2 + x**2), to right
    # (492.6-y)**2 = y**2 + x**2
    # 492.6**2 - 2*492.6*y + y**2 = y**2 + x**2
    # 492.6**2 - 155.6**2 = 2*492.6*y
    # y = (492.6**2 - 155.6**2) / (2*492.6) = 221.72
    # 221.72 - 196 = 25.72, to right/left
    car.next(128.28)  # 120, 350-221.72
    print('左打方向到底')
    car.left(35)
    car.next(90)
    print('回正')
    car.left(-35)


def main():
    ground_ZJZW()
    car = Car(turtle.getscreen(), 270, 178)  # 153/178
    ZJZW(car)
    turtle.done()


if __name__ == '__main__':
    main()
