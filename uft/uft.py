#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2016-10-29
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import re
import os
import sys
import json
import base64
import hashlib
from os import path
from datetime import datetime, timezone


HEAD_BLOCK_SIZE = 4096
LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo

def sha256sum(data):
    h = hashlib.sha256()
    h.update(data)
    return base64.urlsafe_b64encode(h.digest()).decode('utf-8')


def str2ts(s):
    if s.endswith('Z'):
        dt = datetime.fromisoformat(s[:-1]).replace(tzinfo=timezone.utc)
    else:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)
    return dt.timestamp()


def fmtinfo(info):
    dt = datetime.fromtimestamp(info['mtime'], tz=timezone.utc).astimezone()
    return f"{dt.isoformat(timespec='seconds').split('+')[0]} {info.get('size')}\t{info['path']}"


CMDS = {}
def register_command(cls):
    CMDS[cls.__name__.lower()] = cls()
    return cls


@register_command
class ScanDir(object):

    def register(self, parser):
        parser.add_argument('--headhash', '-hh', action='store_true', help='hash mode.')
        parser.add_argument('--dirs-only', '-d', action='store_true', help='show only dir.')
        parser.add_argument('--files-only', '-f', action='store_true', help='show only file.')
        parser.add_argument('--exclude', '-e', action='append', help='exclude dirs.')
        parser.add_argument('dir', nargs='?', type=str)

    def scandir(self, fp):
        st = os.stat(fp)
        return {'path': fp, 'mtime': st.st_mtime, 'isdir': True}

    def scanfile(self, fp):
        st = os.lstat(fp)  # don't follow symbolic link
        info = {'path': fp, 'size': st.st_size, 'mtime': st.st_mtime}
        if self.args.headhash and st.st_size > 100:
            with open(fp, 'rb') as fi:
                info['head_sha256'] = sha256sum(fi.read(HEAD_BLOCK_SIZE))
        return info

    def execute(self):
        for root, dirs, files in os.walk(self.args.dir):
            if self.args.exclude and any(root.startswith(ex) for ex in self.args.exclude):
                continue
            if not self.args.files_only:
                for fn in dirs:
                    fp = path.join(root, fn)
                    self.logger.info(f'scan dir {fp}')
                    self.stdout.write(json.dumps(self.scandir(fp), ensure_ascii=False)+'\n')
            if not self.args.dirs_only:
                for fn in files:
                    fp = path.join(root, fn)
                    self.logger.info(f'scan file {fp}')
                    self.stdout.write(json.dumps(self.scanfile(fp), ensure_ascii=False)+'\n')


@register_command
class ScanRclone(object):

    def register(self, parser):
        parser.add_argument('prefix', nargs='?', type=str)

    def execute(self):
        for info in json.load(self.stdin):
            info['Path'] = self.args.prefix + info['Path']
            if 'Hashes' in info:
                info.update(info['Hashes'])
                del info['Hashes']
            if 'Name' in info:
                del info['Name']
            if 'MimeType' in info:
                del info['MimeType']
            if 'IsDir' in info and not info['IsDir']:
                del info['IsDir']
            if 'IsDir' in info:
                del info['Size']
            info = {k.lower(): v for k, v in info.items()}
            info['mtime'] = str2ts(info.pop('modtime'))
            self.stdout.write(json.dumps(info, ensure_ascii=False)+'\n')


@register_command
class Search(object):

    def register(self, parser):
        parser.add_argument('--files-only', '-f', action='store_true', help='search only file.')
        parser.add_argument('--ignore-case', '-i', help='ignore case.')
        parser.add_argument('pattern', nargs='?', type=str)

    def execute(self):
        pattern = self.args.pattern
        if self.args.ignore_case:
            pattern = pattern.lower()
        self.logger.info(f'pattern: {pattern}')
        r = re.compile(pattern)

        for line in self.stdin:
            info = json.loads(line.strip())
            if self.args.files_only and info.get('isdir'):
                continue
            fp = info.get('path')
            if self.args.ignore_case:
                fp = fp.lower()
            if r.search(fp):
                self.stdout.write(fmtinfo(info)+'\n')


def main():
    import logging
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd')
    for name, cmd in CMDS.items():
        cmd.register(subparsers.add_parser(name, help=f'{name} help'))
    parser.add_argument('--loglevel', '-l', default='warning', help='loglevel')
    args = parser.parse_args()

    cmd = CMDS[args.cmd]
    cmd.args = args
    cmd.stdin, cmd.stdout = sys.stdin, sys.stdout

    cmd.logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    cmd.logger.addHandler(handler)
    cmd.logger.setLevel(args.loglevel.upper())

    cmd.execute()


if __name__ == '__main__':
    import uft
    import uft_dup
    import uft_mount
    uft.main()
