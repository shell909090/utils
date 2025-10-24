#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2022-12-27
@author: Shell.Xu
@copyright: 2022, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from lib import *


def ground_DCRK():  # 倒车入库
    t = setup_world(0, -1007, 1600, 200)  # 682+525-200
    sneaky(t, 0, 200)
    t.fd(1595)  # 1596 = 682*2 + 231
    sneaky(t, 0, -482)
    t.fd(682)
    t.right(90)
    t.fd(525)
    t.left(90)
    t.fd(231)
    t.left(90)
    t.fd(525)
    t.right(90)
    t.fd(682)


def DCRK(car):
    car.next(1325)  # 1325 = 1595 - 270
    print('倒车')
    car.speed = -1
    car.next(1325-1183)  # 1183 = 682 + 231/2 + 385.6(R in 35)
    print('右打方向到底')
    car.left(-35)
    car.next(90)
    print('回正')
    car.left(35)
    car.next(494)  # 494 = 482 - 385.6 + 525/2 + 270/2, 30.75 to bottom, 26.5 to left
    print('出库')
    car.speed = 1
    car.next(494)
    print('左打方向到底')
    car.left(35)
    car.next(90)
    print('回正')
    car.left(-35)


def main():
    ground_DCRK()
    car = Car(turtle.getscreen(), 270, 178)  # 153/178
    DCRK(car)
    turtle.done()


if __name__ == '__main__':
    main()
