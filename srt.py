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


def read_multi_line(fi):
    line = fi.readline().strip()
    while line:
        yield line
        line = fi.readline().strip()


def main():
    with open(sys.argv[1], 'r') as fi:
        for line in fi:
            if '-->' not in line:
                continue
            ti = line.strip().split('-->')[0].split(',')[0]
            s = ' '.join(read_multi_line(fi))
            print(f'{ti} {s}')


if __name__ == '__main__':
    main()
