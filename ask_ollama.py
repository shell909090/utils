#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-03-15
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import re
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
    logging.info(f'get content from url: {url}')
    resp = requests.get(url)
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'html.parser')
    return doc.get_text()


def ask_startpage(query):
    from bs4 import BeautifulSoup
    resp = requests.post('https://www.startpage.com/sp/search', data={'query': query, 't': 'device'})
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'html.parser')
    for a in doc.find_all('a'):
        print(a)


re_think = re.compile('<think>.*</think>', re.DOTALL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--endpoint', '-e', default=os.getenv('OLLAMA_ENDPOINT', 'http://127.0.0.1:11434'), help='ollama endpoint')
    parser.add_argument('--model', '-m', default=os.getenv('CHAT_MODEL', 'deepseek-r1:14b'), help='ollama model')
    parser.add_argument('--from-input', '-fi', action='store_true', help='read background from stdin')
    parser.add_argument('--max-context-length', '-c', default=16384, type=int, help='maximum context length')
    parser.add_argument('--remove-think', '-rt', action='store_true', help='remove think')
    parser.add_argument('--file', '-f', action='append', help='input file')
    parser.add_argument('--url', '-u', action='append', help='source url')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    command = '. '.join(args.rest)
    if not command:
        command = '给代码写注释'
    if args.debug:
        logging.debug(f'command: {command}')

    background = []
    if args.file:
        for fp in args.file:
            with open(fp) as fi:
                logging.info(f'get content from file: {fp}')
                background.append(fi.read())
    if args.url:
        for u in args.url:
            background.append(get_text_from_url(u))
    if args.from_input:
        background.append(sys.stdin.read())

    background = "\n".join(background)
    template = '你是一个个人助理，请阅读<start>到</end>之间的所有内容，帮助用户回答问题。<start>{background}</end>。{command}。'
    prompt = template.format(background=background, command=command)
    if args.debug:
        logging.debug(f'prompt: {prompt}')

    logging.info(f'send request to ollama: {args.endpoint} {args.model}')
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
        response = data['response']
        if args.remove_think:
            response = re_think.sub('', response)
        print(response)
        # 将所有浮点数输出改为小数点后两位格式
        duration_total = data['total_duration'] / 10**9
        prompt_eval_count = data['prompt_eval_count']
        prompt_eval_duration = data['prompt_eval_duration'] / 10**9
        eval_count = data['eval_count']
        eval_duration = data['eval_duration'] / 10**9
        eval_rate = eval_count / eval_duration
        logging.info(f'total_duration: {duration_total:.2f}, prompt_eval_count: {prompt_eval_count}, prompt_eval_duration: {prompt_eval_duration:.2f}, eval_count: {eval_count}, eval_duration: {eval_duration:.2f}, eval_rate: {eval_rate:.2f}')
    else:
        print(resp.status_code, resp.content)


if __name__ == '__main__':
    main()
