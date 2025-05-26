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
from os import path

import requests

import ai


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


def chapter_doc(txt, max_size=8192):
    s = ''
    for line in txt:
        if args.remove_empty_line and not line:
            continue
        if len(s) + len(line) > max_size:
            yield s + '\n' + line  # 重复跨章节内容
            s = line
        else:
            s += '\n' + line
    if s:
        yield s


def summary_chapter(c):
    messages = [
        {'role': 'system', 'content': args.prompt},
        {'role': 'user', 'content': f'<start>{c}</end>'},
    ]
    return provider.chat(args.model, messages, remove_think=True)


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
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'), help='ollama model')
    parser.add_argument('--max-context-length', '-c', type=int, default=8192, help='maximum context length')
    parser.add_argument('--interval', '-iv', type=int, help='let ollama cool down')
    parser.add_argument('--prompt', '-p', default='你是一个AI个人助理，请阅读以下材料，简述主要观点和关键内容。材料以<start>开始，以</end>结束。简述要详细，最好给出引用。无论材料以何种语言书写，你都要用中文总结。')
    parser.add_argument('--translate-file', '-tr', action='store_true')
    parser.add_argument('--remove-empty-line', '-rel', help='remove empty line')
    parser.add_argument('--chapter-output', '-co', help='filename extension of chapters')
    parser.add_argument('--summary-output', '-so', default='.sum', help='filename extension of summary')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    if not args.ollama_endpoint and not args.openai_endpoint:
        args.ollama_endpoint = 'http://127.0.0.1:11434'

    if args.translate_file:
        args.prompt = '你是一个AI个人助理，请阅读以下材料，将内容翻译为中文。材料以<start>开始，以</end>结束。注意保持格式不变。注意保持语气。输出内容仅包括翻译结果。'

    global provider
    provider = ai.make_provider_from_args(args)

    for fp in args.rest:
        if path.exists(fp + args.summary_output):
            logging.error(f'target exists, {fp} has been processed before.')
        doc = source_doc(fp)
        doc = chapter_doc(doc, max_size=args.max_context_length)
        chapter_output = (fp + args.chapter_output) if args.chapter_output else args.chapter_output
        doc = summary_doc(doc, chapter_output)
        with open(fp + args.summary_output, 'a') as fo:
            doc_to_file(fo, doc)


if __name__ == '__main__':
    main()
