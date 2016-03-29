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

def main():
    dictcn.optdict = {'-s': 1, '-p': 1}

    with open(sys.argv[1]) as fi:
        content = fi.read().decode('utf-8-sig')
    wordlist = [line.strip() for line in content.splitlines()]

    with open(sys.argv[1], 'wb') as fi:
        writer = csv.writer(fi)
        for word in wordlist:
            writer.writerow((word, dictcn.query_dict(word)))

if __name__ == '__main__': main()
