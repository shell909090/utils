#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-09-16
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import sys
import argparse

import httpx
from bs4 import BeautifulSoup

import ai


def get_text(u):
    resp = httpx.get(u)
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'lxml')
    for p in doc.select('section.article-body div.article-paragraph'):
        yield p.get_text().strip()


def read_article(provider, args, content):
    prompt = f'你是一个AI个人助理，请阅读以下材料，简述关键内容。材料以<start>开始，以</end>结束。无论材料以何种语言书写，你都要用中文总结。<start>{content}</end>'
    response = provider.generate(args.model, prompt, remove_think=True)
    print(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'), help='model')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    ai.setup_logging()
    provider = ai.make_provider()

    for u in args.rest:
        content = '\n'.join(get_text(u))
        read_article(provider, args, content)


if __name__ == '__main__':
    main()
