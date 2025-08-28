#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2019-03-16
@author: Shell.Xu
@copyright: 2019, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import sys
import argparse

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--css', default='', help='css selector')
    parser.add_argument('-p', '--parser', default='lxml',
                        help="parser, could be {lxml, html5lib, html.parser}.")
    parser.add_argument('-m', '--html', action='store_true', help='output pretty html')
    parser.add_argument('-t', '--text', action='store_true', help='output text')
    parser.add_argument('-a', '--attr', help='output attr')
    parser.add_argument('file', nargs='*', help='input files. read stdin if no file.')
    args = parser.parse_args()

    outputs = sum([1 for i in (args.html, args.text, args.attr) if i])
    if outputs == 0:
        args.html = True
    elif outputs > 1:
        print('output format must be one of the {html, text, attr}.')
        return 1

    def io_search(d):
        doc = BeautifulSoup(d, args.parser)
        if not args.css:
            print(doc.prettify())
            return
        for i in doc.select(args.css):
            if args.html:
                i = i.prettify()
            elif args.text:
                i = i.get_text()
            elif args.attr:
                i = i.attrs.get(args.attr)
            print(i)

    if not args.file:
        io_search(sys.stdin.read())
    else:
        for fn in args.file:
            with open(fn, 'rb') as fi:
                d = fi.read()
            io_search(d)
    return 0


if __name__ == '__main__':
    sys.exit(main())
