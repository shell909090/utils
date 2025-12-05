#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-12-02
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import sys
import logging
import argparse
from hashlib import sha256

import httpx
from bs4 import BeautifulSoup

import ai


def list_image_models(provider):
    for m in provider.list_models():
        if 'predict' in m['supported_actions']:
            print(f'{m["name"]} [gen_image] {m["description"]}')
        elif 'generateContent' in m['supported_actions'] and 'image' in m['name']:
            print(f'{m["name"]} [generate_content] {m["description"]}')


def gen_image(provider, args):
    prompt = '\n'.join(args.rest)
    image = provider.gen_image(args.model, prompt, format=args.format)

    hashtag = sha256((args.model+':'+prompt).encode('utf-8')).hexdigest()[:16]
    logging.info(f'hashtag: {hashtag}')

    filepath = args.output.format(hashtag=hashtag)
    logging.info(f'write output: {filepath}')
    image.save(filepath)


def generate_content(provider, args):
    from PIL import Image
    prompt = '\n'.join(args.rest)

    hashtag = sha256((args.model+':'+prompt).encode('utf-8')).hexdigest()[:16]
    logging.info(f'hashtag: {hashtag}')

    filepath = args.output.format(hashtag=hashtag)
    logging.info(f'write output: {filepath}')

    contents = list(args.rest)
    if args.input_image:
        for fn in args.input_image:
            contents.append(Image.open(fn))

    resp = provider.generate_content(args.model, contents)
    for part in resp.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.as_image()
            image.save(filepath)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'), help='model')
    parser.add_argument('--list-models', '-l', action='store_true')
    parser.add_argument('--input-image', '-i', action='append')
    parser.add_argument('--output', '-o', default='output_{hashtag}.jpg')
    parser.add_argument('--format', '-f', default='image/jpeg')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    ai.setup_logging()
    provider = ai.make_provider()

    if args.list_models:
        list_image_models(provider)
        return

    m = provider.get_model(args.model)
    if 'predict' in m['supported_actions']:
        gen_image(provider, args)
    elif 'generateContent' in m['supported_actions'] and 'image' in args.model:
        generate_content(provider, args)


if __name__ == '__main__':
    main()
