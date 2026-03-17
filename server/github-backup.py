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
import glob
import json
import logging
import argparse
import datetime
import tempfile
import subprocess
from os import path
from urllib.parse import quote, urlparse, urlunparse

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
    resp = requests.get(url, headers=cfg['headers'], timeout=cfg.get('timeout', 60), **kw)
    resp.raise_for_status()
    return resp


def authed_clone_url(cfg, repo):
    parsed = urlparse(repo['clone_url'])
    if parsed.scheme != 'https':
        return repo['clone_url']
    user = quote(cfg.get('git_username', cfg['username']), safe='')
    token = quote(cfg['token'], safe='')
    netloc = f'{user}:{token}@{parsed.hostname}'
    if parsed.port:
        netloc += f':{parsed.port}'
    return urlunparse(parsed._replace(netloc=netloc))


def get_repos(cfg):
    # https://docs.github.com/en/rest/repos/repos
    # https://stackoverflow.com/questions/21907278/github-api-using-repo-scope-but-still-cant-see-private-repos
    repos = []
    # 10000 repos maximum
    for i in range(1, 101):
        params = {'type': 'all', 'per_page': '100', 'page': str(i)}
        resp = geturl(cfg, 'https://api.github.com/user/repos', params=params)
        page_repos = resp.json()
        repos.extend(page_repos)
        if len(page_repos) < 100:
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
    issues = []
    for i in range(1, 10001):
        resp = geturl(cfg, issues_url, params={'state': 'all', 'per_page': '100', 'page': str(i)})
        page_issues = resp.json()
        issues.extend(page_issues)
        if len(page_issues) < 100:
            break
    jsondump(path.join(cfg['dest'], name+'_issues.json'), issues)
    clone_url = authed_clone_url(cfg, repo)
    repo_dir = path.join(cfg['dest'], name)
    if path.exists(repo_dir):
        subprocess.run(['git', '-C', repo_dir, 'remote', 'update'], check=True)
    else:
        subprocess.run(['git', 'clone', '--mirror', clone_url, repo_dir], check=True)


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
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg['dest'] = tmpdir
            backup_repos(cfg)

            curdir = os.getcwd()
            os.chdir(cfg['dest'])
            try:
                subprocess.run(['7z', 'a', cfg['destzip']] + glob.glob('*'), check=True)
            finally:
                os.chdir(curdir)
    else:
        backup_repos(cfg)


if __name__ == '__main__':
    main()
