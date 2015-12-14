#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2015-12-14
@author: Shell.Xu
@copyright: 2015, Shell.Xu <shell909090@gmail.com>
@license: cc
@comment:
    translate original cedict to dictd server acceptable format.

    python cedict.py cedict_file | dictfmt --utf8 -s 'cedict' -j cedict
    dictzip cedict.dict
    mv cedict.dict.dz cedict.index /usr/share/dictd/
'''
import re, sys

re_line = re.compile('^(.*) (.*) \[.*\] /(.*)/$')
def parser(line):
    m = re_line.match(line)
    if not m:
        print line
        raise Exception('not match')
    return m.group(2), m.group(3).split('/')

re_parenthesis = re.compile('\(.*?\)')
def clean_english(eng):
    if '(' in eng or ')' in eng:
        eng = re_parenthesis.sub('', eng).strip()
    if not eng: return
    if ' ' in eng: return
    return eng

def main():
    wd = {}
    with open(sys.argv[1]) as fi:
        for line in fi:
            if line.startswith('#'): continue
            chs, engs = parser(line.strip())
            for eng in engs:
                eng = clean_english(eng)
                if not eng: continue
                wd.setdefault(eng, []).append(chs)

    for k, v in wd.iteritems():
        print ':%s:%s' % (k, ','.join(v))

if __name__ == '__main__': main()
