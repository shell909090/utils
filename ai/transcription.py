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
import math
import time
import logging
import argparse
import tempfile
import subprocess
from os import path

import requests
from gevent.pool import Pool

import ai

# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


re_format = re.compile(r'\[FORMAT\].*duration=(.*)\[/FORMAT\]', re.DOTALL)
def get_duration(fp):
    p = subprocess.run(['ffprobe', '-v', '0', '-show_entries', 'format=duration', fp], capture_output=True)
    stdout = p.stdout.decode('utf-8')
    logging.debug(f'ffprobe output: {stdout}')
    m = re_format.search(stdout)
    if not m:
        raise Exception(f"can't get duration: {stdout}")
    return float(m.group(1).strip())


def pre_processing_audio(fp, i, td):
    logging.info(f'split audio chunk {i}')
    command = ['ffmpeg', '-i', fp, '-ar', '16000', '-ac', '1', '-ss', f'{10*i}:00', '-t', '10:10', f'{td}/{i}.mp3']
    p = subprocess.run(command)
    return f'{td}/{i}.mp3'


def proc_file(provider, fp):
    basefp = path.splitext(fp)[0]
    if path.exists(f'{basefp}.txt'):
        logging.info(f'{fp} has been processed before.')
        return
    duration = get_duration(fp)
    chunks = math.ceil(duration/600)

    if chunks == 1:
        output = provider.transcription(args.model, fp, language=args.language)
        with open(f'{basefp}.txt', 'w') as fo:
            fo.write(output)
        return

    with tempfile.TemporaryDirectory() as td:
        for i in range(chunks):
            tmpfile = pre_processing_audio(fp, i, td)
            output = provider.transcription(args.model, tmpfile, language=args.language)
            with open(f'{basefp}.txt', 'a') as fo:
                fo.write(f'-----{i+1}-----\n\n{output}\n\n')
            time.sleep(5)


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--openai-endpoint', '-ie', default=os.getenv('OPENAI_ENDPOINT'), help='openai endpoint')
    parser.add_argument('--openai-apikey', '-ik', default=os.getenv('OPENAI_APIKEY'), help='openai apikey')
    parser.add_argument('--model', '-m', default=os.getenv('TRANS_MODEL', 'whisper-large-v3'), help='model')
    parser.add_argument('--language', '-lg', default='zh', help='language')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    provider = ai.make_provider_from_args(args)

    for fp in args.rest:
        proc_file(provider, fp)


if __name__ == '__main__':
    main()
