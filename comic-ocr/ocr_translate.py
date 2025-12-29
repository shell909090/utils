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
import zipfile
from io import BytesIO

import pyperclip
import numpy as np
from PIL import ImageGrab, Image
from manga_ocr import MangaOcr
from deep_translator import GoogleTranslator
from openai import OpenAI
from paddleocr import PaddleOCR


SYSTEM_PROMPT = """
你是一位资深的漫画汉化组翻译。
你的任务是将用户提供的日文漫画台词翻译成中文。
要求：
1. 【语境优先】结合漫画常见的口语、省略语和俚语进行意译。
2. 【语气自然】中文表达要符合人物说话的语气。
3. 【格式】直接输出翻译后的中文，不要包含任何解释。
"""

class ImageGenerator(object):

    def __iter__(self) -> Image:
        pass


class ClipboardImageGenerator(ImageGenerator):

    def __iter__(self):
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


class ZipImageGenerator(ImageGenerator):

    def __init__(self, zip_path):
        self.zip_path = zip_path

    def __iter__(self):
        # Image file extensions to look for
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')

        with zipfile.ZipFile(self.zip_path, 'r') as zf:
            # Get all image files sorted by name
            image_files = sorted([
                name for name in zf.namelist()
                if name.lower().endswith(image_extensions) and not name.startswith('__MACOSX')
            ])

            for image_file in image_files:
                try:
                    # Read image data from zip
                    image_data = zf.read(image_file)
                    # Convert to PIL Image
                    img = Image.open(BytesIO(image_data))
                    yield img
                except Exception as e:
                    logging.error(f"Failed to read image {image_file}: {e}")
                    continue


class PaddleOCRTextDetectionCutter(ImageGenerator):

    def __init__(self, image_generator: ImageGenerator, use_angle_cls=True, lang='japan', use_gpu=False, padding=5):
        self.image_generator = image_generator
        self.ocr = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, use_gpu=use_gpu, show_log=False)
        self.padding = padding

    def __iter__(self):
        for img in self.image_generator:
            # Convert PIL Image to numpy array for PaddleOCR
            img_array = np.array(img)

            # Use PaddleOCR to detect text boxes (only detection, no recognition)
            result = self.ocr.ocr(img_array, rec=False)

            if not result or not result[0]:
                continue

            # Get image dimensions
            img_width, img_height = img.size

            # Iterate through detected text boxes
            for box_info in result[0]:
                box = box_info
                # box is a list of 4 points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                # Get bounding box coordinates
                points = np.array(box).astype(np.int32)
                x_min = int(points[:, 0].min())
                y_min = int(points[:, 1].min())
                x_max = int(points[:, 0].max())
                y_max = int(points[:, 1].max())

                # Add padding and ensure within image boundaries
                x_min = max(0, x_min - self.padding)
                y_min = max(0, y_min - self.padding)
                x_max = min(img_width, x_max + self.padding)
                y_max = min(img_height, y_max + self.padding)

                # Crop the image based on bounding box with padding
                cropped_img = img.crop((x_min, y_min, x_max, y_max))
                yield cropped_img


class Translator(object):

    def translate(self, text) -> str:
        pass


class GoogleTranslatorWrapper(Translator):

    def __init__(self, source='auto', target='zh-CN'):
        self.translator = GoogleTranslator(source=source, target=target)

    def translate(self, text):
        if not text.strip():
            return ''
        return self.translator.translate(text)


class OpenAITranslator(Translator):

    def __init__(self, api_key, model, endpoint=None):
        if endpoint:
            self.client = OpenAI(api_key=api_key, base_url=endpoint)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model

    def translate(self, text):
        if not text.strip():
            return ''
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
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
    parser.add_argument('--use-paddle-detection', '-pd', action='store_true', help='use PaddleOCR for text detection and cropping')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    ocr = MangaOcr()
    logging.info('MangaOcr loaded')

    if args.translator_provider == 'google':
        translator = GoogleTranslatorWrapper(source='auto', target=args.target_language)
        logging.info(f'GoogleTranslator loaded, target language is {args.target_language}')
    elif args.translator_provider == 'openai':
        translator = OpenAITranslator(api_key=args.api_key, model=args.model, endpoint=args.endpoint)
        logging.info(f'Use OpenAI service to translate')
    else:
        raise Exception(f'unknown translator provider: {args.translator_provider}')

    if args.rest:
        # Use ZipImageGenerator if a zip file path is provided
        zip_path = args.rest[0]
        image_generator = ZipImageGenerator(zip_path)
        logging.info(f'Reading images from zip file: {zip_path}')
    else:
        # Use ClipboardImageGenerator by default
        image_generator = ClipboardImageGenerator()
        logging.info('Reading images from clipboard')

    if args.use_paddle_detection:
        image_generator = PaddleOCRTextDetectionCutter(image_generator)
        logging.info('PaddleOCR text detection enabled')

    for img in image_generator:
        start_time = time.time()
        jp_text = ocr(img)

        if not jp_text.strip():
            continue

        print(f"原文 (日语): {jp_text}")

        try:
            cn_text = translator.translate(jp_text)
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
