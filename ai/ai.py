#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-04-27
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import re
import sys
import json
import logging

import httpx
from pydantic import BaseModel, Field


def setup_logging():
    """
    设置日志记录器。
    """
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


class Provider(object):
    re_think = re.compile('<think>.*</think>', re.DOTALL)
    re_code = re.compile('```.*')

    def __init__(self, retries):
        transport = httpx.HTTPTransport(retries=retries)
        self.sess = httpx.Client(transport=transport)

    def _send_req(self, url, model, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        if 'json' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            logging.debug(f'req:\n{json.dumps(kwargs["json"], indent=2)}')
        if self.apikey:
            kwargs['headers']['Authorization'] = f'Bearer {self.apikey}'
        logging.info(f'send request to {self.name}: {self.endpoint} {model}')
        resp = self.sess.post(url, **kwargs)
        if resp.status_code >= 400:
            logging.error(resp.content)
        resp.raise_for_status()
        logging.info(f'received response from {self.name}')
        data = resp.json()
        logging.debug(f'resp:\n{json.dumps(data, indent=2)}')
        return data

    def chat(self, model, messages, remove_think=False, **kwargs):
        response = self._chat(model, messages, **kwargs)
        if remove_think:
            response = self.re_think.sub('', response)
        return response

    def generate(self, model, prompt, remove_think=False, **kwargs):
        response = self._generate(model, prompt, **kwargs)
        if remove_think:
            response = self.re_think.sub('', response)
        return response


class OpenAI(Provider):

    name = 'openai'

    def __init__(self, endpoint, apikey=None, retries=3, **kwargs):
        super().__init__(retries)
        self.endpoint = endpoint
        self.apikey = apikey

    def _chat(self, model, messages):
        req = {
            'model': model,
            'stream': False,
            'messages': messages,
        }
        data = self._send_req(f'{self.endpoint}/chat/completions', model, json=req)
        logging.info(json.dumps(data['usage']))
        return data['choices'][0]['message']['content']

    def _generate(self, model, prompt):
        req = {
            'model': model,
            'stream': False,
            'input': prompt,
        }
        data = self._send_req(f'{self.endpoint}/responses', model, json=req)
        logging.info(json.dumps(data['usage']))
        return ''.join(msg['content'][0]['text'] for msg in data['output'] if msg['type'] == 'message')

    def transcription(self, model, fn, f, language='zh'):
        files = {
            'file': (fn, f, 'application/octet-stream'),
            'model': (None, model),
            'temperature': (None, '0'),
            'response_format': (None, 'verbose_json'),
            'language': (None, language),
            # 'timestamp_granularities': (None, '["word"]'),
        }
        return self._send_req(f'{self.endpoint}/audio/transcriptions', model, files=files)['segments']


class Gemini(Provider):
    """
    Google Gemini AI服务提供商的实现。
    """

    name = 'gemini'

    class TranscriptSegment(BaseModel):
        start: float = Field(description="Start time of the segment, number, in second")
        end: float = Field(description="End time of the segment, number, in second")
        text: str = Field(description="The transcribed text for this segment")


    class TranscriptionResponse(BaseModel):
        language: str = Field(description="Detected language of the audio")
        segments: list[TranscriptSegment]

    def __init__(self, endpoint=None, apikey=None, retries=3, **kwargs):
        super().__init__(retries)
        from google import genai
        # self.endpoint = endpoint
        self.apikey = os.getenv('GEMINI_API_KEY')
        self.client = genai.Client()

    def _generate(self, model, prompt, **kwargs):
        resp = self.client.models.generate_content(model=model, contents=prompt)
        return resp.text

    def transcription(self, model, fn, f, language='中文'):
        from google.genai import types
        resp = self.client.models.generate_content(
            model=model,
            contents=[
                f"请完全按照语音内容转录此音频文件，并将输出格式设置为清晰的文本稿。输出语言使用{language}。",
                types.Part.from_bytes(data=f.read(), mime_type="audio/mp3")
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self.TranscriptionResponse # Pass the Pydantic class here
            ))
        return json.loads(resp.text)['segments']


def make_provider():
    if os.getenv('GEMINI_API_KEY'):
        return Gemini()
    elif os.getenv('OPENAI_ENDPOINT'):
        return OpenAI(os.getenv('OPENAI_ENDPOINT'), os.getenv('OPENAI_APIKEY'))
    raise Exception('provider not found in args')
