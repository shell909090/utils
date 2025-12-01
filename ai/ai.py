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
import random
import logging
from os import path

import httpx


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

    def generate(self, model, input, remove_think=False, **kwargs):
        response = self._generate(model, input, **kwargs)
        if remove_think:
            response = self.re_think.sub('', response)
        return response


class Ollama(Provider):

    name = 'ollama'

    def __init__(self, endpoint, apikey=None, max_context_length=8192, num_batch=16, retries=3, **kwargs):
        super().__init__(retries)
        self.endpoint = endpoint
        self.apikey = apikey
        self.max_context_length = max_context_length
        self.num_batch = num_batch

    @staticmethod
    def fmt_ollama_stat(data):
        # 将所有浮点数输出改为小数点后两位格式
        duration_total = data['total_duration'] / 10**9
        prompt_eval_count = data['prompt_eval_count']
        prompt_eval_duration = data['prompt_eval_duration'] / 10**9
        eval_count = data['eval_count']
        eval_duration = data['eval_duration'] / 10**9
        eval_rate = eval_count / eval_duration
        return f'total_duration: {duration_total:.2f}, prompt_eval_count: {prompt_eval_count}, prompt_eval_duration: {prompt_eval_duration:.2f}, eval_count: {eval_count}, eval_duration: {eval_duration:.2f}, eval_rate: {eval_rate:.2f}'

    def _chat(self, model, messages):
        req = {
            'model': model,
            'stream': False,
            'messages': messages,
            'options': {
                'num_ctx': self.max_context_length,
                'num_batch': self.num_batch,
            },
        }
        data = self._send_req(f'{self.endpoint}/api/chat', model, json=req)
        logging.info(self.fmt_ollama_stat(data))
        return data['message']['content']

    def _generate(self, model, input):
        req = {
            'model': model,
            'stream': False,
            'prompt': input,
            'options': {
                'num_ctx': self.max_context_length,
                'num_batch': self.num_batch,
            },
        }
        data = self._send_req(f'{self.endpoint}/api/generate', model, json=req)
        logging.info(self.fmt_ollama_stat(data))
        return data['response']


class OpenAI(Provider):

    name = 'openai'

    def __init__(self, endpoint, apikey=None, retries=3, **kwargs):
        super().__init__(retries)
        self.endpoint = endpoint
        self.apikey = apikey

    @staticmethod
    def fmt_openai_stat(usage):
        return f"total_tokens: {usage['total_tokens']}, prompt_tokens: {usage['prompt_tokens']}, completion_tokens: {usage['completion_tokens']}"

    def _chat(self, model, messages):
        req = {
            'model': model,
            'stream': False,
            'messages': messages,
        }
        data = self._send_req(f'{self.endpoint}/chat/completions', model, json=req)
        logging.info(self.fmt_openai_stat(data['usage']))
        return data['choices'][0]['message']['content']

    def _generate(self, model, input):
        req = {
            'model': model,
            'stream': False,
            'input': input,
        }
        data = self._send_req(f'{self.endpoint}/responses', model, json=req)
        logging.info(self.fmt_openai_stat(data['usage']))
        return data['output'][0]['content']['text']

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

    def __init__(self, endpoint, apikey=None, retries=3, **kwargs):
        super().__init__(retries)
        self.endpoint = endpoint
        self.apikey = apikey

    def _send_gemini_req(self, url, model, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        if 'json' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            logging.debug(f'req:\n{json.dumps(kwargs["json"], indent=2)}')
        if self.apikey:
            kwargs['headers']['x-goog-api-key'] = self.apikey
        logging.info(f'send request to {self.name}: {self.endpoint} {model}')
        resp = self.sess.post(url, **kwargs)
        if resp.status_code >= 400:
            logging.error(resp.content)
        resp.raise_for_status()
        logging.info(f'received response from {self.name}')
        data = resp.json()
        logging.debug(f'resp:\n{json.dumps(data, indent=2)}')
        return data

    def _chat(self, model, messages, thinking_budget=None):
        contents = []
        for message in messages:
            role = message.get('role')
            content = message.get('content')
            if not role or not content:
                continue
            # Gemini API expects 'user' or 'model' roles, mapping 'assistant' to 'model'
            gemini_role = 'model' if role == 'assistant' else role
            contents.append({
                'role': gemini_role,
                'parts': [{'text': content}]
            })

        req_body = {"contents": contents}
        if thinking_budget is not None:
            req_body['generationConfig'] = {
                "thinkingConfig": {
                    "thinkingBudget": thinking_budget
                }
            }
        url = f'{self.endpoint}/models/{model}:generateContent'
        resp = self._send_gemini_req(url, model, json=req_body)

        # Extracting the response content
        response_text = ""
        if resp and 'candidates' in resp and resp['candidates']:
            for candidate in resp['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            response_text += part['text']
        return response_text

    def _generate(self, model, input_text, thinking_budget=None):
        messages = [{'role': 'user', 'content': input_text}]
        return self._chat(model, messages, thinking_budget)


def make_provider():
    if os.getenv('OLLAMA_ENDPOINT'):
        return Ollama(os.getenv('OLLAMA_ENDPOINT'), os.getenv('OLLAMA_APIKEY'), os.getenv('MAX_CONTEXT_LENGTH'))
    elif os.getenv('OPENAI_ENDPOINT'):
        return OpenAI(os.getenv('OPENAI_ENDPOINT'), os.getenv('OPENAI_APIKEY'))
    elif os.getenv('GEMINI_APIKEY'):
        return Gemini('https://generativelanguage.googleapis.com/v1beta', os.getenv('GEMINI_APIKEY'))
    elif os.getenv('GROQ_APIKEY'):
        return OpenAI('https://api.groq.com/openai/v1', os.getenv('GROQ_APIKEY'))
    elif os.getenv('OPENROUTER_APIKEY'):
        return OpenAI('https://openrouter.ai/api/v1', os.getenv('OPENROUTER_APIKEY'))
    else:
        raise Exception('provider not found in args')
