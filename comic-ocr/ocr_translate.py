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
from paddleocr import TextDetection


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

    def __init__(self, zip_path, output_file=None):
        self.zip_path = zip_path
        self.output_file = output_file

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
                    logging.info(f"Processing image: {image_file}")

                    # Write filename to output file if provided
                    if self.output_file:
                        self.output_file.write(f"\n## {image_file}\n")
                        self.output_file.flush()

                    yield img
                except Exception as e:
                    logging.error(f"Failed to read image {image_file}: {e}")
                    continue


class PaddleOCRTextDetection(object):

    def __init__(self, padding=5, ai_merge_client=None, ai_merge_model=None):
        # TextDetection uses lang and device through **kwargs
        self.detector = TextDetection(device='cpu')
        self.ocr = MangaOcr()
        self.padding = padding
        self.ai_merge_client = ai_merge_client
        self.ai_merge_model = ai_merge_model

    def __call__(self, img: Image) -> str:
        # Convert PIL Image to numpy array for TextDetection
        img_array = np.array(img)

        # Use TextDetection to detect text boxes
        result = self.detector.predict(img_array)

        if not result or not result[0]:
            return ''

        # Extract detected polygons from result
        dt_polys = result[0].get('dt_polys', [])
        if len(dt_polys) == 0:
            return ''

        # Get image dimensions
        img_width, img_height = img.size

        # Sort dt_polys: right to left (for Japanese manga), top to bottom
        # Calculate center point for each box for sorting
        boxes_with_centers = []
        for box in dt_polys:
            points = np.array(box).astype(np.int32)
            center_x = int(points[:, 0].mean())
            center_y = int(points[:, 1].mean())
            boxes_with_centers.append((box, center_x, center_y))

        # Sort by Y (top to bottom) first, then by X (right to left) within same row
        # Group by approximate rows (using Y // 50 for row grouping)
        sorted_boxes = sorted(boxes_with_centers, key=lambda b: (b[2] // 50, -b[1]))

        # Collect recognized text from all detected boxes
        texts = []
        for box, _, _ in sorted_boxes:
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

            # Recognize text in the cropped image
            text = self.ocr(cropped_img)
            if text.strip():
                texts.append(text)

        if not texts:
            return ''

        # Use AI to merge text fragments if client is provided
        if self.ai_merge_client and self.ai_merge_model:
            fragments_input = '\n'.join([f"Fragment {i+1}: {text}" for i, text in enumerate(texts)])
            merge_prompt = f"""你是一个专业的漫画汉化助手。
我将发给你一页漫画中提取出的【零散文本片段】（按从右到左、从上到下的阅读顺序排列）。
请执行以下步骤：
1. 【拼合】：根据日语语法和漫画语境，将断裂的句子、跨气泡的对话重新合并成完整的句子。
2. 【输出】：输出合并后的完整句子，每行一句。不要输出 Fragment 编号，不要输出任何解释。

输入：
{fragments_input}

输出："""

            try:
                completion = self.ai_merge_client.chat.completions.create(
                    model=self.ai_merge_model,
                    messages=[
                        {"role": "user", "content": merge_prompt}
                    ],
                    temperature=0.3,
                )
                merged_text = completion.choices[0].message.content.strip()
                return merged_text
            except Exception as e:
                logging.error(f"AI merge failed: {e}, falling back to concatenation")
                return ''.join(texts)
        else:
            # Concatenate all recognized text without AI merge
            return ''.join(texts)


class PaddleOCRTextDetectionCutter(ImageGenerator):

    def __init__(self, image_generator: ImageGenerator, padding=5):
        self.image_generator = image_generator
        # TextDetection uses lang and device through **kwargs
        self.detector = TextDetection(device='cpu')
        self.padding = padding

    def __iter__(self):
        for img in self.image_generator:
            # Convert PIL Image to numpy array for TextDetection
            img_array = np.array(img)

            # Use TextDetection to detect text boxes
            result = self.detector.predict(img_array)

            if not result or not result[0]:
                continue

            # Extract detected polygons from result
            dt_polys = result[0].get('dt_polys', [])
            if len(dt_polys) == 0:
                continue

            # Get image dimensions
            img_width, img_height = img.size

            # Iterate through detected text boxes
            for box in dt_polys:
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
    parser.add_argument('--output-file', '-o', type=str, help='output file to write translation results')
    parser.add_argument('--log-level', '-l', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='set logging level (default: INFO)')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    # Configure logging level (force=True to override any existing configuration)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(levelname)s: %(message)s',
        force=True
    )

    # Initialize OCR engine
    if args.use_paddle_detection:
        # Create OpenAI client for AI merge if using openai translator
        ai_merge_client = None
        ai_merge_model = None
        if args.api_key and args.model:
            if args.endpoint:
                ai_merge_client = OpenAI(api_key=args.api_key, base_url=args.endpoint)
            else:
                ai_merge_client = OpenAI(api_key=args.api_key)
            ai_merge_model = args.model

        ocr = PaddleOCRTextDetection(ai_merge_client=ai_merge_client, ai_merge_model=ai_merge_model)
        logging.info('PaddleOCR text detection and recognition loaded')
    else:
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

    # Open output file if specified
    output_file = None
    if args.output_file:
        output_file = open(args.output_file, 'w', encoding='utf-8')
        logging.info(f'Writing results to: {args.output_file}')

    if args.rest:
        # Use ZipImageGenerator if a zip file path is provided
        zip_path = args.rest[0]
        image_generator = ZipImageGenerator(zip_path, output_file=output_file)
        logging.info(f'Reading images from zip file: {zip_path}')
    else:
        # Use ClipboardImageGenerator by default
        image_generator = ClipboardImageGenerator()
        logging.info('Reading images from clipboard')

    try:
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

            # Write to output file if specified
            if output_file:
                output_file.write(f"原文: {jp_text}\n")
                output_file.write(f"译文: {cn_text}\n")
                output_file.flush()

            if args.copy_back:
                pyperclip.copy(cn_text)
                logging.info("translate copy back")
    finally:
        if output_file:
            output_file.close()
            logging.info(f'Output file closed: {args.output_file}')



if __name__ == '__main__':
    main()
