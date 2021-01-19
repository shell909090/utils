#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2020-12-31
@author: Shell.Xu
@copyright: 2020, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
@comment:
translate srt to txt file
将srt文件转换为txt文件，容易阅读。
python3 srt.py [srt file]
'''
import sys


def main():
    with open(sys.argv[1], 'r') as fi:
        while True:
            num = fi.readline().strip()
            if not num:
                break
            ti = fi.readline().strip()
            ti = ti.split('-->')[0].split(',')[0]
            s = fi.readline().strip()
            fi.readline()
            print(f'{ti} {s}')


if __name__ == '__main__':
    main()
