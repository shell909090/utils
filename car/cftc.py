#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2022-12-27
@author: Shell.Xu
@copyright: 2022, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from lib import *


# 侧方位库长7.85米，库宽2.5米。倒车入库库宽2.3米，库长5.3米，路宽6.85米；
def ground_CFTC():  # 侧方停车
    t = setup_world(0, -370, 1100, 220)
    sneaky(t, 0, 217)
    t.fd(1100)
    sneaky(t, 0, -120)  # 30 to right
    t.fd(1100)
    sneaky(t, 0, -120)
    t.goto(0, -370)
    t.fd(785)
    t.left(90)
    t.fd(250)


def CFTC(car):
    # 47 - 0 - 800, 30 - 280 - 840
    angle = 30
    distance = 280
    car.next(840)
    print('倒车')
    car.speed = -1
    print('右打方向到底')
    car.left(-35)
    car.next(angle)
    print('回正')
    car.left(35)
    car.next(distance)
    print('左打方向到底')
    car.left(35)
    car.next(angle)
    print('回正')
    car.left(-35)


def main():
    ground_CFTC()
    car = Car(turtle.getscreen(), 270, 178)  # 153/178
    CFTC(car)
    turtle.done()


if __name__ == '__main__':
    main()
