#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2016-03-24
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os, sys
import csv
import dictcn
import binascii

def main():
    dictcn.optdict = {'-w': ''}

    with open(sys.argv[1]) as fi:
        content = fi.read().decode('utf-8-sig')
    wordlist = [line.strip() for line in content.splitlines()]

    with open(sys.argv[2], 'wb') as fi:
        writer = csv.writer(fi)
        for word in wordlist:
            word = word.strip().lower()
            print word, '...',
            info = dictcn.query_dict(word)
            if info['keyword'].lower() != str(word):
                raise Exception('dismatch', info['keyword'], str(word))
            writer.writerow((
                word.lower(),
                dictcn.format_result(info)))
            print 'ok'

if __name__ == '__main__': main()
