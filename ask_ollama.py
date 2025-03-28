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
import json
import logging
import argparse
from os import path

import requests
from gevent.pool import Pool

def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


def get_text_from_url(url, ignore_status=False):
    from bs4 import BeautifulSoup
    logging.info(f'get content from url: {url}')
    resp = requests.get(url)
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'html.parser')
    return doc.get_text(" ", strip=True)


def ask_startpage(query):
    from bs4 import BeautifulSoup
    resp = requests.post('https://www.startpage.com/sp/search', data={'query': query, 't': 'device'})
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'html.parser')
    for a in doc.find_all('a'):
        print(a)


def duckduckgo(q):
    from duckduckgo_search import DDGS
    results = DDGS().text(q, max_results=args.search_engine_max_results)
    return [r['href'] for r in results]


def ask_search_engine(command, search_engine):
    results = search_engine(command)
    pool = Pool(args.search_engine_max_results)
    def f(r):
        try:
            return get_text_from_url(r)
        except:
            return
    return [doc for doc in pool.imap(f, results) if doc]


re_think = re.compile('<think>.*</think>', re.DOTALL)


def fmt_stat(data):
    # 将所有浮点数输出改为小数点后两位格式
    duration_total = data['total_duration'] / 10**9
    prompt_eval_count = data['prompt_eval_count']
    prompt_eval_duration = data['prompt_eval_duration'] / 10**9
    eval_count = data['eval_count']
    eval_duration = data['eval_duration'] / 10**9
    eval_rate = eval_count / eval_duration
    return f'total_duration: {duration_total:.2f}, prompt_eval_count: {prompt_eval_count}, prompt_eval_duration: {prompt_eval_duration:.2f}, eval_count: {eval_count}, eval_duration: {eval_duration:.2f}, eval_rate: {eval_rate:.2f}'


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--endpoint', '-e', default=os.getenv('OLLAMA_ENDPOINT', 'http://127.0.0.1:11434'), help='ollama endpoint')
    parser.add_argument('--model', '-m', default=os.getenv('CHAT_MODEL', 'deepseek-r1:14b'), help='ollama model')
    parser.add_argument('--from-input', '-fi', action='store_true', help='read background from stdin')
    parser.add_argument('--max-context-length', '-c', type=int, default=32768, help='maximum context length')
    parser.add_argument('--remove-think', '-rt', action='store_true', help='remove think')
    parser.add_argument('--file', '-f', action='append', help='input file')
    parser.add_argument('--url', '-u', action='append', help='source url')
    parser.add_argument('--search-duckduckgo', '-sd', action='store_true', help='search duckduckgo as source')
    parser.add_argument('--search-engine-max-results', '-semr', type=int, default=3, help='max results for refer')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    global options
    options = {
        'num_ctx': args.max_context_length,
        'num_batch': 16,
    }

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
    if args.search_duckduckgo:
        background.extend(ask_search_engine(command, duckduckgo))

    if args.debug:
        for b in background:
            logging.debug(f'background: {b}')

    background = ['<start>%s</end>' % doc for doc in background]
    messages = [
        {
            'role': 'system',
            'content': '你是一个AI个人助理，请阅读以下材料，帮助用户回答问题。每篇材料以<start>开始，以</end>结束。\n'+'\n'.join(background)
        },
        {'role': 'user', 'content': command}
    ]

    logging.info(f'send request to ollama: {args.endpoint} {args.model}')
    resp = requests.post(f'{args.endpoint}/api/chat', json={
        'model': args.model,
        'stream': False,
        'messages': messages,
        'options': options,
    })
    resp.raise_for_status()
    logging.info('received response from ollama')

    data = resp.json()
    if args.debug:
        logging.debug(f'response: {json.dumps(data, indent=2)}')
    response = data['message']['content']
    if args.remove_think:
        response = re_think.sub('', response)
    print(response)
    logging.info(fmt_stat(data))


if __name__ == '__main__':
    main()
