#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2016-03-07
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause

Copyright (C) 2016 Shell Xu

@comment:

在dict.cn上查询关键词，并解析返回结果，以文本界面的方式提供。

注：返回内容的版权归dict.cn所有。

'''
import os, sys
import getopt
import cStringIO
import requests
from bs4 import BeautifulSoup

def currying(func, param):
    def inner(*params):
        return func(param, *params)
    return inner

def write_node(stream, node, strip=True):
    stream.write(node.get_text(strip=strip).encode('utf-8')+'\n')

def query_dict(words):
    resp = requests.get('http://dict.cn/' + words)
    if resp.status_code != 200:
        raise Exception(resp.status_code)

    doc = BeautifulSoup(resp.content, 'lxml')
    unfind = doc.find('div', class_='unfind')
    if unfind is not None:
        return unfind.get_text().encode('utf-8')

    output = cStringIO.StringIO()
    write = currying(write_node, output)
    if '-p' not in optdict:
        phonetic = doc.find('div', class_='phonetic')
        if phonetic:
            map(write, phonetic.find_all('span'))

    basic = doc.find('div', class_='basic')
    if basic:
        map(write, [li for li in basic.find_all('li') if 'style' not in li.attrs])

    if '-s' not in optdict:
        shape = doc.find('div', class_='shape')
        if shape:
            map(write, shape.find_all('span'))

    return output.getvalue().strip()

def main():
    ''' dictcn.py [-h] [-p] [-s] word '''
    optlist, argv = getopt.getopt(sys.argv[1:], 'hps')
    global optdict
    optdict = dict(optlist)
    if '-h' in optdict:
        print main.__doc__

    print query_dict(argv[0])

if __name__ == '__main__': main()
