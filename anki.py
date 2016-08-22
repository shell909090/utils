#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2016-03-24
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys
import csv
import codecs
import dictcn
import binascii

def data_source(wordlist):
    for word in wordlist:
        word = word.strip().lower()

        print('{0}...'.format(word), end='')
        info = dictcn.query_dict(word)
        if info['keyword'].lower() != str(word):
            raise Exception('dismatch', info['keyword'], str(word))
        print('ok')
        
        yield word, dictcn.format_result(info)

def main():
    dictcn.optdict = {'-w': ''}

    with codecs.open(sys.argv[1], 'r', 'utf-8-sig') as fi:
        content = fi.read()
    wordlist = [line.strip() for line in content.splitlines()]

    data = data_source(wordlist)

    with open(sys.argv[2], 'w') as fi:
        writer = csv.writer(fi)
        for row in data:
            if sys.version_info.major == 2:
                row = (row[0].encode('utf-8'), row[1].encode('utf-8'))
            writer.writerow(row)

if __name__ == '__main__': main()
