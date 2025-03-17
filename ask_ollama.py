#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-03-15
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import sys
import logging
import argparse
from os import path

import requests


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


def get_text_from_url(url):
    from bs4 import BeautifulSoup
    resp = requests.get(url)
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'html.parser')
    return doc.get_text()


def ask_startpage(query):
    from bs4 import BeautifulSoup
    resp = requests.post(f'https://www.startpage.com/sp/search', data={'query': query, 't': 'device'})
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'html.parser')
    for a in doc.find_all('a'):
        print(a)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--endpoint', '-e', default=os.getenv('OLLAMA_ENDPOINT', 'http://127.0.0.1:11434'), help='ollama endpoint')
    parser.add_argument('--model', '-m', default=os.getenv('CHAT_MODEL', 'deepseek-r1:14b'), help='ollama model')
    parser.add_argument('--max-context-length', '-c', default=16384, type=int, help='maximum context length')
    parser.add_argument('--file', '-f', help='input file')
    parser.add_argument('--url', '-u', help='source url')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    command = '. '.join(args.rest)
    if not command:
        command = '给代码写注释'
    if args.debug:
        logging.debug(f'command: {command}')

    background = []
    if args.file and path.exists(args.file):
        with open(args.file) as fi:
            background.append(fi.read())

    if args.url:
        background.append(get_text_from_url(args.url))

    background = "\n".join(background)
    template = '你是一个个人助理，请阅读<start>到</end>之间的所有内容，帮助用户回答问题。<start>{background}</end>。{command}。'
    prompt = template.format(background=background, command=command)
    if args.debug:
        logging.debug(f'prompt: {prompt}')

    resp = requests.post(f'{args.endpoint}/api/generate', json={
        'model': args.model,
        'stream': False,
        'prompt': prompt,
        'options': {
            'num_ctx': args.max_context_length,
        },
    })

    if resp.status_code == 200:
        data = resp.json()
        print(data['response'])
        logging.info(f"total_duration: {data['total_duration']/(10**9)}, prompt_eval_count: {data['prompt_eval_count']}, prompt_eval_duration: {data['prompt_eval_duration']/(10**9)}, eval_count: {data['eval_count']}, eval_duration: {data['eval_duration']/(10**9)}, speed: {10**9*data['eval_count']/data['eval_duration']}")
    else:
        print(resp.status_code, resp.content)


if __name__ == '__main__':
    main()
