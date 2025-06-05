#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-03-15
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from gevent import monkey
monkey.patch_all()

import os
import re
import sys
import json
import math
import time
import random
import shutil
import logging
import argparse
import datetime
import tempfile
import subprocess
from os import path

import requests
from gevent.pool import Pool

import ai

# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1


class Writer(object):

    def __init__(self, fp):
        self.f = open(fp, 'w')
        self.i = 0

    def close(self):
        self.f.close()


class TxtWriter(Writer):

    def write(self, segment):
        self.f.write(segment['text']+'\n')
        self.f.flush()


class SrtWriter(Writer):

    @staticmethod
    def fmt_time(t):
        s = int(t) % 60
        m = int(int(t) / 60)
        return f'{int(m / 60):02}:{m % 60:02}:{s:02},{int(t*1000) % 1000:03}'

    def write(self, segment):
        self.i += 1
        self.f.write(f'{self.i}\n{self.fmt_time(segment["start"])} --> {self.fmt_time(segment["end"])}\n{segment["text"].strip()}\n\n')
        self.f.flush()


re_format = re.compile(r'\[FORMAT\].*duration=(.*)\[/FORMAT\]', re.DOTALL)
def get_duration(fp):
    p = subprocess.run(['ffprobe', '-v', '0', '-show_entries', 'format=duration', fp], capture_output=True)
    stdout = p.stdout.decode('utf-8')
    logging.debug(f'ffprobe output: {stdout}')
    m = re_format.search(stdout)
    if not m:
        raise Exception(f"can't get duration: {stdout}")
    return float(m.group(1).strip())


re_silence_start = re.compile('.*silence_start: (.*)')
def detect_silence(fp, db=30, duration=0.5):
    logging.info('detect silence')
    command = ['ffmpeg', '-i', fp, '-af', f'silencedetect=n=-{db}dB:d={duration}', '-f', 'null', '-']
    p = subprocess.run(command, capture_output=True)
    stderr = p.stderr.decode('utf-8')
    for line in stderr.splitlines():
        line = line.strip()
        if not line.startswith('[silencedetect'):
            continue
        m = re_silence_start.match(line)
        if m:
            yield float(m.group(1))


def pick_gaps(gaps, max_chunk_duration=600):
    s = max_chunk_duration
    while len(gaps) > 1:
        if gaps[0] > s:
            raise Exception(f'gap oversize: {gaps[0]} / {s}')
        if gaps[1] >= s:
            s = gaps[0] + max_chunk_duration
            yield gaps[0]
        gaps.pop(0)
    if gaps[0] > s:
        raise Exception(f'gap oversize: {gaps[0]} / {s}')
    yield gaps[0]


def cut_off_audio(fp):
    duration = get_duration(fp)
    gaps = list(detect_silence(fp, args.db))
    gaps.append(duration)
    logging.debug(f'gaps1: {gaps}')
    gaps = list(pick_gaps(gaps, args.max_chunk_duration))
    gaps.insert(0, 0)
    logging.debug(f'gaps2: {gaps}')
    return gaps


def pre_processing_audio(src, i, start, end, dst):
    logging.info(f'split audio chunk {i}, start: {start}, end: {end}, duration: {end-start}')
    if path.exists(dst):
        logging.info(f'audio chunk exists: {dst}')
        return
    logging.info(f'create audio chunk: {dst}')
    command = ['ffmpeg', '-i', src, '-ar', '16000', '-ac', '1',
               '-ss', str(datetime.timedelta(seconds=start)),
               '-to', str(datetime.timedelta(seconds=end)),
               dst]
    p = subprocess.run(command, stderr=subprocess.DEVNULL)


def transcription_chunk(provider, chunkfile, segfile):
    if path.exists(segfile):
        logging.info(f'load segments: {segfile}')
        with open(segfile) as fi:
            return json.load(fi)

    logging.info(f'waiting {args.interval} seconds')
    time.sleep(args.interval)

    with open(chunkfile, 'rb') as fi:
        segments = provider.transcription(
            random.choice(args.models), path.basename(chunkfile), fi, language=args.language)

    logging.info(f'dump segments: {segfile}')
    with open(segfile, 'w') as fo:
        json.dump(segments, fo)
    return segments


def transcription(provider, fp):
    if args.load_temp:
        tmpdir = args.load_temp
        logging.info(f'load gaps: {tmpdir}/gaps.json')
        with open(path.join(tmpdir, 'gaps.json')) as fi:
            gaps = json.load(fi)
    else:
        tmpdir = tempfile.mkdtemp()
        logging.info(f'use tmpdir: {tmpdir}')
        gaps = cut_off_audio(fp)
        logging.info(f'dump gaps: {tmpdir}/gaps.json')
        with open(path.join(tmpdir, 'gaps.json'), 'w') as fo:
            json.dump(gaps, fo)

    logging.info(f'audio will be splited to {len(gaps)-1} chunks')
    i = 0
    while len(gaps) > 1:
        chunkfile = f'{tmpdir}/{i}.mp3'
        pre_processing_audio(fp, i, gaps[0], gaps[1], chunkfile)

        segfile = f'{tmpdir}/{i}.json'
        segments = transcription_chunk(provider, chunkfile, segfile)

        for s in segments:
            s['start'] += gaps[0]
            s['end'] += gaps[0]
            yield s

        i += 1
        gaps.pop(0)

    if args.clean_up_temp:
        logging.info(f'cleanup tmpdir: {tmpdir}')
        shutil.rmtree(tmpdir)


def proc_file(provider, fp):
    basefp = path.splitext(fp)[0]
    if not args.force_overwrite and (path.exists(f'{basefp}.txt') or path.exists(f'{basefp}.srt')):
        logging.info(f'{fp} has been processed before.')
        return
    logging.info(f'process {fp}')

    writers = []
    if not args.disable_txt:
        logging.info(f'write txt to {basefp}.txt')
        writers.append(TxtWriter(f'{basefp}.txt'))
    if not args.disable_srt:
        logging.info(f'write srt to {basefp}.srt')
        writers.append(SrtWriter(f'{basefp}.srt'))

    try:
        for s in transcription(provider, fp):
            for w in writers:
                w.write(s)
    finally:
        for w in writers:
            w.close()


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', '-m', default=os.getenv('TRANS_MODELS', 'whisper-large-v3'), help='models')
    parser.add_argument('--language', '-l', default='zh', help='language')
    parser.add_argument('--load-temp', '-lt', help='load everything from temp dir')
    parser.add_argument('--clean-up-temp', '-ct', action='store_true', help='clean up temp dir after finish')
    parser.add_argument('--max-chunk-duration', '-mcd', type=int, default=300, help='maximum seconds one audio chunk could have')
    parser.add_argument('--interval', '-i', type=int, default=10, help='wait between each API call')
    parser.add_argument('--force-overwrite', '-y', action='store_true')
    parser.add_argument('--db', '-db', type=int, default=35, help='db to detect silence')
    parser.add_argument('--disable-txt', '-dt', action='store_true')
    parser.add_argument('--disable-srt', '-ds', action='store_true')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    ai.setup_logging()
    args.models = args.models.split(',')

    provider = ai.make_provider()

    for fp in args.rest:
        proc_file(provider, fp)


if __name__ == '__main__':
    main()
