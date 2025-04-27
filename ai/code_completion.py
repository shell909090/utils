#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-04-27
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

import ai

# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv)


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', '-l', default='INFO', help='log level')
    parser.add_argument('--ollama-endpoint', '-ae', default=os.getenv('OLLAMA_ENDPOINT'), help='ollama endpoint')
    parser.add_argument('--openai-endpoint', '-ie', default=os.getenv('OPENAI_ENDPOINT'), help='openai endpoint')
    parser.add_argument('--openai-apikey', '-ik', default=os.getenv('OPENAI_APIKEY'), help='openai apikey')
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'), help='model')
    parser.add_argument('--max-context-length', '-c', type=int, default=16384, help='maximum context length')
    parser.add_argument('--remove-think', '-rt', action='store_true', help='remove think')
    args = parser.parse_args()

    setup_logging(args.log_level.upper())

    if not args.ollama_endpoint and not args.openai_endpoint:
        args.ollama_endpoint = 'http://127.0.0.1:11434'

    provider = ai.make_provider_from_args(args)

    messages = [
        {'role': 'user', 'content': '你是一个AI代码助理，你要帮助用户补全他的代码。代码以<code>开始，以</code>结束。当前光标所在位置是{{CURSOR}}。你需要在这个位置，写上你认为合适的代码。输出应当只包含补全代码，注意缩进对齐。'},
    ]
    code = sys.stdin.read()
    messages.append({'role': 'user', 'content': f'<code>{code}</code>'})

    response = provider.chat(args.model, messages, remove_think=args.remove_think)
    response = provider.re_code.sub('', response)
    print(response)


if __name__ == '__main__':
    main()
