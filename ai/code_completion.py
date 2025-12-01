#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-04-27
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import sys
import argparse

import ai


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'), help='model')
    parser.add_argument('--remove-think', '-rt', action='store_true', help='remove think')
    args = parser.parse_args()

    ai.setup_logging()
    provider = ai.make_provider()

    code = sys.stdin.read()
    prompt = f'你是一个AI代码助理，你要帮助用户补全他的代码。代码以<code>开始，以</code>结束。当前光标所在位置是{{CURSOR}}。你需要在这个位置，写上你认为合适的代码。输出应当只包含补全代码，注意缩进对齐。<code>{code}</code>'

    response = provider.generate(args.model, prompt, remove_think=args.remove_think)
    response = provider.re_code.sub('', response)
    print(response)


if __name__ == '__main__':
    main()
