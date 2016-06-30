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

def get_node_str(node):
    return node.get_text(strip=True).encode('utf-8')

def get_nodes_str(nodes):
    return '\n'.join(map(get_node_str, nodes))

def query_dict(words):
    resp = requests.get('http://dict.cn/' + words)
    if resp.status_code != 200:
        raise Exception(resp.status_code)

    doc = BeautifulSoup(resp.content, 'lxml')
    unfind = doc.find('div', class_='unfind')
    if unfind is not None:
        return unfind.get_text().encode('utf-8')

    result = {}

    keyword = doc.find('h1', class_='keyword')
    if keyword:
        result['keyword'] = get_node_str(keyword)

    phonetic = doc.find('div', class_='phonetic')
    if phonetic:
        result['phonetic'] = get_nodes_str(phonetic.find_all('span'))

    basic = doc.find('div', class_='basic')
    if basic:
        result['basic'] = get_nodes_str([
            li for li in basic.find_all('li') if 'style' not in li.attrs])

    shape = doc.find('div', class_='shape')
    if shape:
        result['shape'] = get_nodes_str(shape.find_all('span'))

    return result

def currying(func, param):
    def inner(*params):
        return func(param, *params)
    return inner

def write_node(stream, node, strip=True):
    stream.write(node.get_text(strip=strip).encode('utf-8')+'\n')

def format_result(info):
    output = cStringIO.StringIO()

    if '-w' not in optdict:
        keyword = info.get('keyword')
        if keyword:
            output.write(keyword + '\n')

    if '-p' not in optdict:
        phonetic = info.get('phonetic')
        if phonetic:
            output.write(phonetic + '\n')

    basic = info.get('basic')
    if basic:
        output.write(basic + '\n')

    if '-s' not in optdict:
        shape = info.get('shape')
        if shape:
            output.write(shape + '\n')

    return output.getvalue().strip()

def main():
    ''' dictcn.py [-h] [-p] [-s] word '''
    optlist, args = getopt.getopt(sys.argv[1:], 'hpsw')
    global optdict
    optdict = dict(optlist)
    if '-h' in optdict:
        print main.__doc__

    for arg in args:
        info = query_dict(arg)
        print format_result(info)

if __name__ == '__main__': main()
