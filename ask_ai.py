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

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
}


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


def get_text_from_url(url, raise_status=False):
    from bs4 import BeautifulSoup
    logging.info(f'get content from url: {url}')
    resp = requests.get(url, headers=headers)
    if raise_status:
        resp.raise_for_status()
    elif resp.status_code >= 400:
        logging.error(f'error when get content from url: {url} {resp.status_code}')
        return
    doc = BeautifulSoup(resp.text, 'html.parser')
    return doc.get_text('\n', strip=True)


def get_text_from_urls(urls, concurrent=5, raise_status=False):
    pool = Pool(concurrent)
    docs = pool.imap(lambda u: get_text_from_url(u, raise_status), urls)
    return [doc for doc in docs if doc]


def duckduckgo(q, max_results=5):
    from duckduckgo_search import DDGS
    results = DDGS().text(q, max_results=max_results)
    return [r['href'] for r in results]


def fmt_ollama_stat(data):
    # 将所有浮点数输出改为小数点后两位格式
    duration_total = data['total_duration'] / 10**9
    prompt_eval_count = data['prompt_eval_count']
    prompt_eval_duration = data['prompt_eval_duration'] / 10**9
    eval_count = data['eval_count']
    eval_duration = data['eval_duration'] / 10**9
    eval_rate = eval_count / eval_duration
    return f'total_duration: {duration_total:.2f}, prompt_eval_count: {prompt_eval_count}, prompt_eval_duration: {prompt_eval_duration:.2f}, eval_count: {eval_count}, eval_duration: {eval_duration:.2f}, eval_rate: {eval_rate:.2f}'


def ollama_chat(messages):
    logging.info(f'send request to ollama: {args.ollama_endpoint} {args.model}')
    resp = requests.post(f'{args.ollama_endpoint}/api/chat', json={
        'model': args.model,
        'stream': False,
        'messages': messages,
        'options': options,
    })
    resp.raise_for_status()
    logging.info('received response from ollama')
    data = resp.json()
    logging.info(fmt_ollama_stat(data))
    return data['message']['content']


def fmt_openai_stat(usage):
    return f"total_tokens: {usage['total_tokens']}, prompt_tokens: {usage['prompt_tokens']}, completion_tokens: {usage['completion_tokens']}"


def openai_chat(messages):
    headers = {
        'Content-Type': 'application/json',
    }
    if args.openai_apikey:
        headers['Authorization'] = f'Bearer {args.openai_apikey}'
    logging.info(f'send request to openai: {args.openai_endpoint} {args.model}')
    resp = requests.post(f'{args.openai_endpoint}/chat/completions', headers=headers, json={
        'model': args.model,
        'stream': False,
        'messages': messages,
    })
    resp.raise_for_status()
    logging.info('received response from openai')
    data = resp.json()
    logging.info(fmt_openai_stat(data['usage']))
    return data['choices'][0]['message']['content']

re_think = re.compile('<think>.*</think>', re.DOTALL)
def ai_chat(messages, remove_think=False):
    if args.ollama_endpoint:
        response = ollama_chat(messages)
    else:
        response = openai_chat(messages)
    if args.debug:
        logging.debug(f'response: {response}')
    if remove_think:
        response = re_think.sub('', response)
    return response


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--ollama-endpoint', '-ae', default=os.getenv('OLLAMA_ENDPOINT'), help='ollama endpoint')
    parser.add_argument('--openai-endpoint', '-ie', default=os.getenv('OPENAI_ENDPOINT'), help='openai endpoint')
    parser.add_argument('--openai-apikey', '-ik', default=os.getenv('OPENAI_APIKEY'), help='openai apikey')
    parser.add_argument('--model', '-m', default=os.getenv('CHAT_MODEL', 'deepseek-r1:14b'), help='model')
    parser.add_argument('--from-input', '-fi', action='store_true', help='read background from stdin')
    parser.add_argument('--max-context-length', '-c', type=int, default=32768, help='maximum context length')
    parser.add_argument('--remove-think', '-rt', action='store_true', help='remove think')
    parser.add_argument('--file', '-f', action='append', help='input file')
    parser.add_argument('--url', '-u', action='append', help='source url')
    parser.add_argument('--search-duckduckgo', '-ddgs', action='store_true', help='search duckduckgo as source')
    parser.add_argument('--search-engine-max-results', '-semr', type=int, default=5, help='max results for refer')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    if not args.ollama_endpoint and not args.openai_endpoint:
        args.ollama_endpoint = 'http://127.0.0.1:11434'

    global options
    options = {
        'num_ctx': args.max_context_length,
        'num_batch': 16,
    }

    command = '. '.join(args.rest)
    if not command:
        logging.error('no command')
        return
    if args.debug:
        logging.debug(f'command: {command}')

    background = []

    if args.file:
        for fp in args.file:
            with open(fp) as fi:
                logging.info(f'get content from file: {fp}')
                background.append(fi.read())

    if args.url:
        background.extend(get_text_from_urls(args.url, len(args.url), raise_status=True))

    if args.from_input:
        background.append(sys.stdin.read())

    if args.search_duckduckgo:
        urls = duckduckgo(command, args.search_engine_max_results)
        for u in urls:
            logging.info(f'search result url: {u}')
        background.extend(get_text_from_urls(urls, args.search_engine_max_results))

    if args.debug:
        for b in background:
            logging.debug(f'background: {b}')

    messages = [
        {'role': 'system', 'content': '你是一个AI个人助理，请阅读以下材料，帮助用户回答问题。每篇材料以<start>开始，以</end>结束。回答问题的时候，需要给出每篇材料的原始信息引用和位置。'}
    ]
    for doc in background:
        messages.append({'role': 'user', 'content': f'<start>{doc}</end>'})
    messages.append({'role': 'user', 'content': command})

    response = ai_chat(messages, args.remove_think)
    print(response)


if __name__ == '__main__':
    main()
