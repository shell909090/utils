#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2022-12-27
@author: Shell.Xu
@copyright: 2022, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from lib import *


def ground_DC():  # 倒车
    t = setup_world(0, -750, 1000, 400)
    sneaky(t, 0, 380)
    t.fd(1000)
    sneaky(t, 0, 130)
    t.fd(1000)
    sneaky(t, 0, -120)
    t.fd(375)
    t.right(90)
    t.fd(600)
    t.left(90)
    t.fd(250)
    t.left(90)
    t.fd(600)
    t.right(90)
    t.fd(375)


def DC1(car):
    car.next(340)  # 基本就是前轮和库前角重合，不到一点 (375+250-270)=355
    print('左转打到底')
    car.left(35)
    car.next(45)
    print('倒车，右转打到底')
    car.speed = -1
    car.left(-70)
    car.next(45)
    print('回正倒车')
    car.left(35)
    car.next(414)


# def DC1(car):
#     car.next(370)
#     print('左转打到底')
#     car.left(35)
#     car.next(55)
#     car.where_am_i()
#     print('回正倒车')
#     car.left(-35)
#     car.speed = -1
#     car.next(200)
#     print('右转打到底')
#     car.left(-35)
#     car.next(35)
#     print('回正倒车')
#     car.left(35)
#     car.next(353)
#     car.where_am_i()


def DC2(car):
    car.next(440)
    print('左转打到底')
    car.left(35)
    car.next(35)
    car.where_am_i()
    print('倒车，右转打到底')
    car.speed = -1
    car.left(-70)
    car.next(55)
    print('回正倒车')
    car.left(35)
    car.next(368)
    car.where_am_i()


# def DC2(car):
#     car.next(430)
#     print('左转打到底')
#     car.left(35)
#     car.next(35)
#     car.where_am_i()
#     print('倒车，右转打到底')
#     car.speed = -1
#     car.left(-70)
#     car.next(60)
#     print('回正倒车，修正位置')
#     car.left(35)
#     car.next(80)
#     print('左转到底，倒车，修正位置')
#     car.left(35)
#     car.next(5)
#     print('回正倒车')
#     car.left(-35)
#     car.next(180)
#     car.where_am_i()


def main():
    ground_DC()
    car = Car(turtle.getscreen(), 270, 178)  # 153/178
    DC1(car)
    # car = Car(turtle.getscreen(), 270, 178)  # 153/178
    # DC2(car)
    turtle.done()


if __name__ == '__main__':
    main()
