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
import json
import gzip
from os import path

import uft


@uft.register_command
class FindDup(object):

    def register(self, parser):
        parser.add_argument('--snapshot', '-ss', action='append', help='use snapshot file.')
        parser.add_argument('--no-name', '-nn', action='store_true', help="don't compare by name.")
        parser.add_argument('--size', '-s', action='store_true', help='compare by size.')
        parser.add_argument('--mtime', '-m', action='store_true', help='compare by mtime.')
        parser.add_argument('--hash', '-hh', action='store_true', help='compare by hash.')
        parser.add_argument('--interactive', '-i', action='store_true', help='interactively remove.')
        parser.add_argument('--copies', '-c', type=int, default=2, help='at least n copies.')

    def group(self, stdin):
        for line in stdin:
            info = json.loads(line.strip())
            if info.get('isdir'):
                continue
            fp = info['path']
            fn = path.basename(fp)
            key = []
            if not self.args.no_name:
                key.append(fn)
            if self.args.size:
                key.append(info['size'])
            if self.args.mtime:
                key.append(info['mtime'])
            if self.args.hash:
                if 'md5' in info:
                    key.append(info['md5'])
                elif 'head_sha256' in info:
                    key.append(info['head_sha256'])
            self.unique.setdefault(tuple(key), []).append(info)

    def select_file(self, v):
        print('enter you choice to keep: ', end='')
        s = input().lower()
        if s in ('all', 'pass', 'a', 'p'):
            return
        elif s in ('none', 'n'):
            exclude = []
        else:
            exclude = set(int(c)-1 for c in s.split(','))
        for i, info in enumerate(v):
            if i not in exclude:
                os.unlink(info['path'])

    def execute(self):
        self.unique = {}
        if self.args.snapshot:
            for snapshot in self.args.snapshot:
                self.logger.info(f'load snapshot: {snapshot}')
                with gzip.open(snapshot) as stdin:
                    self.group(stdin)
        else:
            self.group(self.stdin)

        for k, v in self.unique.items():
            if len(v) < self.args.copies:
                continue
            self.stdout.write('----------\n')
            for info in v:  # sort v
                self.stdout.write(uft.fmtinfo(info)+'\n')
            if self.args.interactive:
                self.select_file(v)


def group(data, by, min, max, index=None):
    if index is None:
        index = {}
    for d in data:
        for i in by(d):
            index.setdefault(i, []).append(d)
    for i, ds in index.items():
        if len(ds) >= min and len(ds) <= max:
            yield i, ds


@uft.register_command
class FuzzyDup(object):

    def register(self, parser):
        parser.add_argument('--snapshot', '-ss', action='append', help='use snapshot file.')
        parser.add_argument('--min-chunk', '-mik', type=int, default=3, help='at least n chars in a chunk.')
        parser.add_argument('--min-copies', '-mic', type=int, default=2, help='at least n copies.')
        parser.add_argument('--max-copies', '-mxc', type=int, default=10, help='at most n copies.')

    re_cut = re.compile(r'[\W_]+')
    re_sexp_list = [
        ('(', re.compile(r'\((.*?)\)')),
        ('[', re.compile(r'\[(.*?)\]')),
        ('【', re.compile(r'【(.*?)】')),
    ]
    def cut(self, s):
        s, ext = path.splitext(s)
        keys = set()
        def addkey(m):
            if len(m.group(1)) >= self.args.min_chunk:
                keys.add(m.group(1))
            return ''
        for keyword, re_sexp in self.re_sexp_list:
            if keyword in s:
                s = re_sexp.sub(addkey, s)
        for c in self.re_cut.split(s):
            if len(c) >= self.args.min_chunk:
                keys.add(c)
        return ext, keys

    def load(self, stdin):
        for line in stdin:
            info = json.loads(line.strip())
            if info.get('isdir'):
                continue
            fp = info['path']
            info['ext'], info['chunks'] = self.cut(path.basename(fp))
            self.objs[fp] = info

    def regroup(self, chunk, infos):
        index = {}
        for info in infos:
            for c in info['chunks']:
                if c != chunk \
                   and len(self.index[c]) >= self.args.min_copies \
                   and len(self.index[c]) <= self.args.max_copies:
                    index.setdefault(c, []).append(info)
        for k, v in index.items():
            if len(v) > 1:
                self.unique.add(tuple(sorted(info['path'] for info in v)))

    def execute(self):
        self.objs = {}
        if self.args.snapshot:
            for snapshot in self.args.snapshot:
                self.logger.info(f'load snapshot: {snapshot}')
                with gzip.open(snapshot) as stdin:
                    self.load(stdin)
        else:
            self.load(self.stdin)

        chunk_index = {}
        unique = set()
        for common_chunk, info_chunk_grp in group(self.objs.values(), lambda info: info['chunks'], 
                                                  self.args.min_copies, self.args.max_copies, chunk_index):
            def by(info):
                chunks = []
                for c in info['chunks']:
                    if c != common_chunk \
                       and len(chunk_index[c]) >= self.args.min_copies \
                       and len(chunk_index[c]) <= self.args.max_copies:
                        chunks.append(c)
                return chunks
            for common_ext, info_chunk_ext_grp in group(info_chunk_grp, lambda info: [info['ext'],],
                                                        self.args.min_copies, self.args.max_copies):
                for next_chunk, info_grp in group(info_chunk_ext_grp, by,
                                                  self.args.min_copies, self.args.max_copies):
                    unique.add(tuple(sorted(info['path'] for info in info_grp)))

        for fp_list in unique:
            info_list = [self.objs[fp] for fp in fp_list]
            self.stdout.write('----------\n')
            for info in info_list:
                self.stdout.write(uft.fmtinfo(info)+'\n')
