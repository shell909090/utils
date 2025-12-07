#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-12-05
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import sys
import time
import logging
import argparse

import pyperclip
from PIL import ImageGrab, Image
from manga_ocr import MangaOcr
from deep_translator import GoogleTranslator
from openai import OpenAI


SYSTEM_PROMPT = """
你是一位资深的漫画汉化组翻译。
你的任务是将用户提供的日文漫画台词翻译成中文。
要求：
1. 【语境优先】结合漫画常见的口语、省略语和俚语进行意译。
2. 【语气自然】中文表达要符合人物说话的语气。
3. 【格式】直接输出翻译后的中文，不要包含任何解释。
"""


def get_img_from_clipboard():
    last_image = None
    while True:
        time.sleep(0.5)

        try:
            img = ImageGrab.grabclipboard()
        except Exception:
            img = None

        if not isinstance(img, Image.Image):
            continue
        if last_image == img:
            continue

        last_image = img
        yield img


def translate_with_openai(client, args, text):
    if not text.strip():
        return ''
    try:
        completion = client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.8,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[API 请求出错: {e}]"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--translator-provider', '-p', default='google', help='could be "google" or "openai"')
    parser.add_argument('--target-language', '-t', default='zh-CN')
    parser.add_argument('--model', '-m', default=os.getenv('MODEL'))
    parser.add_argument('--api-key', '-k', default=os.getenv('OPENAI_APIKEY'))
    parser.add_argument('--endpoint', '-e', default=os.getenv('OPENAI_ENDPOINT'))
    parser.add_argument('--copy-back', '-cb', action='store_true', help='copy the result of translate back to clipboard')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    ocr = MangaOcr()
    logging.info('MangaOcr loaded')

    if args.translator_provider == 'google':
        translator = GoogleTranslator(source='auto', target=args.target_language)
        logging.info(f'GoogleTranslator loaded, target language is {args.target_language}')
    elif args.translator_provider == 'openai':
        if args.endpoint:
            client = OpenAI(api_key=args.api_key, base_url=args.endpoint)
        else:
            client = OpenAI(api_key=args.api_key)
        logging.info(f'Use OpenAI service to translate')
    else:
        raise Exception(f'unknown translator provider: {args.translator_provider}')

    for img in get_img_from_clipboard():
        start_time = time.time()
        jp_text = ocr(img)

        if not jp_text.strip():
            continue

        print(f"原文 (日语): {jp_text}")

        try:
            if args.translator_provider == 'google':
                cn_text = translator.translate(jp_text)
            elif args.translator_provider == 'openai':
                cn_text = translate_with_openai(client, args, jp_text)
        except Exception as e:
            logging.error(e)
            continue

        print(f"译文 (中文): \033[1;32m{cn_text}\033[0m") # 绿色文字显示
        logging.info(f"耗时: {time.time() - start_time:.2f}s")

        if args.copy_back:
            pyperclip.copy(cn_text)
            logging.info("translate copy back")



if __name__ == '__main__':
    main()
