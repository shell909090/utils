#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2012-03-23
@author: shell.xu
'''
import gevent
from gevent import pool, monkey
monkey.patch_all()

import argparse
import time
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag

from bs4 import BeautifulSoup
# from lxml import etree
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


def download(url, **kw):
    logging.info(f'download {url}')
    headers = {'user-agent': USER_AGENT}
    # kw['verify'] = False
    kw.setdefault('timeout', 30)
    resp = session.get(url, headers=headers, **kw)
    resp.raise_for_status()
    time.sleep(1)
    return resp


def save_pic(url, filename):
    resp = download(url)
    filename.write_bytes(resp.content)


def main():
    parser = argparse.ArgumentParser(description='Download images from HTML img tags.')
    parser.add_argument('urls', nargs='+')
    parser.add_argument('-o', '--output', type=Path, default=Path('.'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    p = pool.Pool(5)
    jobs = []
    seen = set()
    filenames = set()
    for url in args.urls:
        resp = download(url)
        baseurl = resp.url
        doc = BeautifulSoup(resp.text, 'lxml')
        base = doc.find('base', href=True)
        if base:
            baseurl = urljoin(baseurl, base['href'])
        for img in doc.select('img'):
            src = (img.get('lazyload-src') or img.get('data-src')
                   or img.get('file') or img.get('src'))
            if not src:
                continue
            image_url = urldefrag(urljoin(baseurl, src))[0]
            if urlparse(image_url).scheme not in ('http', 'https'):
                logger.warning('Skipping non-HTTP image: %s', image_url[:100])
                continue
            if image_url in seen:
                continue
            seen.add(image_url)
            name = Path(urlparse(image_url).path).name
            if name in ('', '.', '..'):
                name = 'image'
            filename = args.output / name
            index = 1
            while filename in filenames or filename.exists():
                filename = args.output / f'{Path(name).stem}-{index}{Path(name).suffix}'
                index += 1
            filenames.add(filename)
            jobs.append(p.spawn(save_pic, image_url, filename))
    p.join()
    failures = sum(not job.successful() for job in jobs)
    logger.info('Downloaded %d images; %d failed', len(jobs) - failures, failures)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
