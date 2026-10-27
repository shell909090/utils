#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2012-03-23
@author: shell.xu
'''
import gevent
from gevent import pool, monkey
monkey.patch_all()

import os
import sys
import time
import logging
import tempfile
import subprocess
from os import path

import bs4
import requests

logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36'


session = requests.Session()
session.mount("http://", requests.adapters.HTTPAdapter(max_retries=3))
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))


def download(url):
    headers = {'user-agent': USER_AGENT}
    resp = session.get(url, headers=headers)
    logging.info('downloaded %s.' % url)
    return resp


def get_img(tmpdir, url, ctr):
    data = download(url).text
    doc = bs4.BeautifulSoup(data, 'lxml')
    for img in doc.select('img#img'):
        filename = '%0.4d-%s' % (ctr, path.basename(img['src']))
        filepath = path.join(tmpdir, filename)
        data = download(img['src']).content
        with open(filepath, 'wb') as fo:
            fo.write(data)


def get_title(doc):
    title_str = ''
    for title in doc.select('h1#gj'):
        title_str = title.get_text().strip()
    if not title_str:
        for title in doc.select('h1#gn'):
            title_str = title.get_text().strip()
    title_str = title_str.replace('/', '_')
    return title_str


def get_page(baseurl):
    p = pool.Pool(5)
    ctr = 1
    tmpdir = tempfile.mkdtemp()
    for page in range(0, 1000):
        if page == 0:
            url = '%s?nw=always' % baseurl
        else:
            url = '%s?p=%d' % (baseurl, page)
        data = download(url).text
        doc = bs4.BeautifulSoup(data, 'lxml')
        for a in doc.select('div#gdt a'):
            time.sleep(1)
            p.spawn(get_img, tmpdir, a['href'], ctr)
            ctr += 1
        if page == 0:
            title = get_title(doc)
        if '>' in set([td.get_text() for td in doc.select('table.ptb td.ptdd')]):
            break
    p.join()

    curdir = os.getcwd()
    os.chdir(tmpdir)
    try:
        zipfilepath = path.join(curdir, title + '.zip')
        subprocess.call(['zip', '-r', zipfilepath, '.'])
    finally:
        os.chdir(curdir)


def main():
    baseurls = sys.argv[1:]
    for baseurl in baseurls:
        get_page(baseurl)


if __name__ == '__main__':
    main()
