#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-03-15
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from gevent import monkey
monkey.patch_all()

import os
import re
import sys
import logging
import argparse
from os import path

import requests
from gevent.pool import Pool

# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


def openai_transcription(fp):
    headers = {}
    if args.openai_apikey:
        headers['Authorization'] = f'Bearer {args.openai_apikey}'
    logging.info(f'read file: {fp}')
    with open(fp, 'rb') as fi:
        files = {
            'file': (path.basename(fp), fi, 'application/octet-stream'),
            'model': (None, args.model),
            'temperature': (None, '0'),
            'response_format': (None, 'verbose_json'),
            'language': (None, args.language),
            # 'timestamp_granularities': (None, '["word"]'),
        }
        logging.info(f'send request to groq: {args.openai_endpoint} {args.model}')
        resp = requests.post(f'{args.openai_endpoint}/audio/transcriptions', headers=headers, files=files)
        logging.info('received response from groq')
    if resp.status_code >= 400:
        logging.error(resp.content)
    resp.raise_for_status()
    data = resp.json()
    return '\n'.join((s['text'] for s in data['segments']))


def proc_file(fp):
    basefp = path.splitext(fp)[0]
    if path.exists(f'{basefp}.txt'):
        logging.info(f'{fp} has been processed before.')
        return
    output = openai_transcription(fp)
    with open(f'{basefp}.txt', 'w') as fo:
        fo.write(output)


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--openai-endpoint', '-ie', default=os.getenv('OPENAI_ENDPOINT'), help='openai endpoint')
    parser.add_argument('--openai-apikey', '-ik', default=os.getenv('OPENAI_APIKEY'), help='openai apikey')
    parser.add_argument('--model', '-m', default=os.getenv('MODEL', 'whisper-large-v3'), help='model')
    parser.add_argument('--language', '-lg', default='zh', help='language')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    for fp in args.rest:
        proc_file(fp)

if __name__ == '__main__':
    main()
