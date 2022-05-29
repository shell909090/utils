#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2019-07-30
@author: Shell.Xu
@copyright: 2019, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
@comment:
  pre-dependence: 7z, git
  config: username, token, dest, ignores, onlyuser, zip
'''
import os
import sys
import json
import logging
import argparse
import datetime
import tempfile
import subprocess
from os import path
from urllib.parse import urlparse, ParseResult

import requests


logger = logging.getLogger()
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)


def jsonload(fp):
    with open(fp, 'r') as fi:
        return json.load(fi)


def jsondump(fp, obj):
    with open(fp, 'w') as fo:
        json.dump(obj, fo)


def geturl(cfg, url, **kw):
    logger.info(f'get {url}')
    return requests.get(url, headers=cfg['headers'], **kw)


def get_repos(cfg):
    # https://docs.github.com/en/rest/repos/repos
    # https://stackoverflow.com/questions/21907278/github-api-using-repo-scope-but-still-cant-see-private-repos
    repos = []
    # 10000 repos maximum
    for i in range(100):
        params = {'type': 'all', 'per_page': '100', 'page': str(i)}
        resp = geturl(cfg, 'https://api.github.com/user/repos', params=params)
        repos.extend(resp.json())
        if len(resp.json()) < 100:
            break
    if cfg.get('onlyuser', True):
        repos = [repo for repo in repos if repo['owner']['login'] == cfg['username']]
    return repos


def grab_repo(cfg, repo):
    # https://zhuanlan.zhihu.com/p/358721423
    # git config --global user.name "shell909090"
    # git config --global credential.helper store
    # 并且实际输入一次密码让git生成~/.git-credentials文件
    name = repo['name']
    logger.info('grab %s' % name)
    issues_url = repo['issues_url'][:-9]
    resp = geturl(cfg, issues_url)
    jsondump(path.join(cfg['dest'], name+'_issues.json'), resp.json())
    subprocess.run(['git', 'clone', '--mirror', repo['clone_url'], path.join(cfg['dest'], name)])


def backup_repos(cfg):
    repos = get_repos(cfg)
    jsondump(path.join(cfg['dest'], cfg['username']+'_repos.json'), repos)
    ignores = set(cfg.get('ignores', []))
    for repo in repos:
        if repo['name'] in ignores:
            continue
        grab_repo(cfg, repo)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', default='~/.github-backup.json')
    parser.add_argument('--loglevel', '-l', default='INFO')
    parser.add_argument('dest', nargs='?', help='destdir')
    args = parser.parse_args()

    cfg = jsonload(path.expanduser(args.config))
    logger.setLevel(args.loglevel or cfg.get('loglevel'))

    cfg['headers'] = {'Authorization': 'token '+cfg['token']}
    if args.dest:
        cfg['dest'] = args.dest
    now = datetime.datetime.now()
    cfg['dest'] = path.abspath(path.expanduser(now.strftime(cfg['dest'])))
    logger.debug(cfg)

    if cfg.get('zip', True):
        cfg['destzip'] = cfg['dest']
        tmpdir = tempfile.TemporaryDirectory()
        cfg['dest'] = tmpdir.name

    backup_repos(cfg)

    if cfg.get('zip', True):
        curdir = os.getcwd()
        os.chdir(cfg['dest'])
        subprocess.run(['7z', 'a', cfg['destzip'], "*"])
        os.chdir(curdir)


if __name__ == '__main__':
    main()
