#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-05-27
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import re
import sys
import time
import logging
import argparse
from os import path

import ai


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


re_time = re.compile('(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)')
def read_srt(fp):
    idx = None
    start = None
    end = None
    text = ''

    with open(fp) as fi:
        for line in fi:
            line = line.strip()

            if not line:
                yield {'index': idx, 'start': start, 'end': end, 'text': text.rstrip()}
                idx = None
                start = None
                end = None
                text = ''
                continue

            if not idx:
                idx = int(line)
                continue

            m = re_time.match(line)
            if m:
                start = 3600*int(m.group(1)) + 60*int(m.group(2)) + int(m.group(3)) + int(m.group(4))/1000
                end = 3600*int(m.group(5)) + 60*int(m.group(6)) + int(m.group(7)) + int(m.group(8))/1000
            else:
                text += line + '\n'


def fmt_time(t):
    s = int(t) % 60
    m = int(int(t) / 60)
    return f'{int(m / 60):02}:{m % 60:02}:{s:02},{int(t*1000) % 1000:03}'


def write_srt(fp, segments):
    with open(fp, 'w') as fo:
        for s in segments:
            fo.write(f"{s['index']}\n{fmt_time(s['start'])} --> {fmt_time(s['end'])}\n{s['text']}\n\n")


def park_segments(segments, max_context_length=8192):
    p = ''
    translate_segments = []
    while segments:
        s = segments[0]
        text = s['text'].replace('\n', ' ')
        t = f"{s['index']}|{text}"
        if len(p) + len(t) > max_context_length:
            return p.strip(), translate_segments
        p += t + '\n'
        translate_segments.append(segments.pop(0))
    return p.strip(), translate_segments


def translate_park(p):
    logging.debug(f'original:{p}')
    messages = [
        {'role': 'system', 'content': args.prompt},
        {'role': 'user', 'content': f'<start>{p}</end>'},
    ]
    q = provider.chat(args.model, messages, remove_think=True)
    logging.debug(f'translated:{q}')

    for line in q.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            idx, text = line.split('|', 1)
            yield int(idx), text
        except ValueError:
            pass


def translate_segments(segments):
    while segments:
        p, translate_segments = park_segments(segments)
        logging.info(f'translate {len(translate_segments)} segments')

        translated = dict(translate_park(p))
        logging.info(f'{len(translated)} segments translated')

        for s in translate_segments:
            if s['index'] not in translated:
                logging.warning(f'index {s["index"]} not been translated')
                segments.append(s)
                continue

            if args.comparative:
                s['text'] += '\n' + translated[s['index']]
            else:
                s['text'] = translated[s['index']]
            yield s

        logging.info('waiting 10 seconds')
        time.sleep(10)


def proc_srt(fp):
    logging.info(f'translate {fp}')
    if path.exists(fp+'.tr'):
        logging.error('file has been processed')
        return

    segments = list(read_srt(fp))
    logging.info(f'{len(segments)} segments readed')
    translated = translate_segments(segments)
    translated = sorted(translated, key=lambda s: s['index'])
    write_srt(fp+'.tr', translated)
    logging.info(f'{len(translated)} segments wrote')


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--ollama-endpoint', '-ae', default=os.getenv('OLLAMA_ENDPOINT'), help='ollama endpoint')
    parser.add_argument('--openai-endpoint', '-ie', default=os.getenv('OPENAI_ENDPOINT'), help='openai endpoint')
    parser.add_argument('--openai-apikey', '-ik', default=os.getenv('OPENAI_APIKEY'), help='openai apikey')
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'), help='ollama model')
    parser.add_argument('--comparative', '-c', action='store_true', help='output both original text and translated')
    parser.add_argument('--language', '-lg', default='中文')
    parser.add_argument('--prompt', '-p', default='你是一个AI个人助理，请阅读以下材料，将内容翻译为{language}。材料以<start>开始，以</end>结束。注意保持格式不变。注意保持语气。输出内容仅包括翻译结果。')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    if not args.ollama_endpoint and not args.openai_endpoint:
        args.ollama_endpoint = 'http://127.0.0.1:11434'

    args.prompt = args.prompt.format(language=args.language)

    global provider
    provider = ai.make_provider_from_args(args)

    for fp in args.rest:
        proc_srt(fp)


if __name__ == '__main__':
    main()
