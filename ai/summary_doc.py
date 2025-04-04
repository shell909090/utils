#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-04-01
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import re
import os
import sys
import time
import logging
import argparse

import requests


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


def source_doc(fp):
    with open(fp) as fi:
        for line in fi:
            yield line.rstrip()


def paragraf_doc(txt):
    s = ''
    for line in txt:
        if not line:
            yield s
            s = ''
        else:
            s += '\n' + line
    if s:
        yield s


def chapter_doc(txt, max_size=8192):
    s = ''
    for p in txt:
        if len(s) + len(p) > max_size:
            yield s + p  # 重复跨章节段落
            s = p
        else:
            s += p
    if s:
        yield s


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
        'options': {
            'num_ctx': args.max_context_length,
            'num_batch': 16,
        },
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


def summary_chapter(c):
    messages = [
        {'role': 'system', 'content': '你是一个AI个人助理，请阅读以下材料，简述主要观点和关键内容。材料以<start>开始，以</end>结束。简述要详细，最好给出引用。无论材料以何种语言书写，你都要用中文总结。'},
        {'role': 'user', 'content': f'<start>{c}</end>'},
    ]
    return ai_chat(messages, True)


def summary_doc(doc, fp=None):
    if fp:
        fo = open(fp, 'a')
    else:
        fo = None
    for i, c in enumerate(doc):
        if fo:
            fo.write(f'-----{i+1}-----\n\n{c}\n\n')
            fo.flush()
        logging.info(f'summary chapter {i+1}, size: {len(c)}')
        yield summary_chapter(c)
    if fo:
        fo.close()


def doc_to_file(fo, doc):
    for i, d in enumerate(doc):
        fo.write(f'-----{i+1}-----\n\n{d}\n\n')
        fo.flush()
        if args.interval:
            time.sleep(args.interval)


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode')
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--ollama-endpoint', '-ae', default=os.getenv('OLLAMA_ENDPOINT'), help='ollama endpoint')
    parser.add_argument('--openai-endpoint', '-ie', default=os.getenv('OPENAI_ENDPOINT'), help='openai endpoint')
    parser.add_argument('--openai-apikey', '-ik', default=os.getenv('OPENAI_APIKEY'), help='openai apikey')
    parser.add_argument('--model', '-m', default=os.getenv('MODEL', 'deepseek-r1:14b'), help='ollama model')
    parser.add_argument('--max-context-length', '-c', type=int, default=8192, help='maximum context length')
    parser.add_argument('--interval', '-iv', type=int, help='let ollama cool down')
    parser.add_argument('--chapter-output', '-co', help='filename of chapters')
    parser.add_argument('--summary-output', '-so', default='summary.txt', help='filename of summary')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    if not args.ollama_endpoint and not args.openai_endpoint:
        args.ollama_endpoint = 'http://127.0.0.1:11434'

    for fp in args.rest:
        doc = source_doc(fp)
        doc = paragraf_doc(doc)
        doc = chapter_doc(doc, max_size=args.max_context_length)
        doc = summary_doc(doc, args.chapter_output)
        with open(args.summary_output, 'a') as fo:
            doc_to_file(fo, doc)


if __name__ == '__main__':
    main()
