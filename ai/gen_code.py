#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-09-23
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

# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'), help='model')
    parser.add_argument('--output', '-o', help='output file')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    ai.setup_logging()
    provider = ai.make_provider()

    messages = []

    for fp in args.rest:
        with open(fp) as fi:
            messages.append({'role': 'user', 'content': fi.read()})

    response = provider.chat(args.model, messages, remove_think=True)
    response = provider.re_code.sub('', response)

    with open(args.output, 'w') as fo:
        fo.write(response.strip())


if __name__ == '__main__':
    main()
