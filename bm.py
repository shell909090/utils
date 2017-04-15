#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2017-04-10
@author: Shell.Xu
@copyright: 2017, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from __future__ import absolute_import, division,\
    print_function, unicode_literals
import sys
import codecs
import getopt

from bs4 import BeautifulSoup


def parse_entry(line):
    line = line.strip()
    if not line.startswith('<DT><A'):
        return
    doc = BeautifulSoup(line[4:], 'html5lib')
    return doc.a


def de_duplicated(bmfilename):
    urls = set()
    with codecs.open(bmfilename, encoding='utf-8') as fi:
        for line in fi:
            line = line.rstrip('\r\n')
            a = parse_entry(line)
            if not a:
                yield line
                continue
            if a['href'] in urls:
                print(a.string, a['href'])
                continue
            urls.add(a['href'])
            yield line


def proc_bm(bmfilename):
    data = '\n'.join(de_duplicated(bmfilename))
    with codecs.open(bmfilename, 'wb', encoding='utf-8') as fi:
        fi.write(data)


def main():
    optlist, args = getopt.getopt(sys.argv[1:], '')
    optdict = dict(optlist)
    if '-h' in optdict:
        print(main.__doc__)
        return

    for bmfilename in args:
        proc_bm(bmfilename)


if __name__ == '__main__':
    main()
