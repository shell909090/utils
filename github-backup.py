#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2019-07-30
@author: Shell.Xu
@copyright: 2019, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from __future__ import absolute_import, division,\
    print_function, unicode_literals
import os
import json
import shutil
import argparse
import datetime
import tempfile
import subprocess
import configparser
from os import path

import requests


USERNAME = ''
TOKEN = ''
DESTDIR = ''


def jsondump(filename, obj):
    with open(path.join(DESTDIR, filename), 'w') as fo:
        json.dump(obj, fo)


def grab_repo(repo):
    name = repo['name']
    print('grab %s' % name)
    issues_url = repo['issues_url'][:-9]
    resp = requests.get(issues_url, headers=HEADERS)
    jsondump(name+'_issues.json', resp.json())
    subprocess.run(['git', 'clone', '--mirror',
                    repo['git_url'], path.join(DESTDIR, name)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    parser.add_argument('-u', '--username')
    parser.add_argument('dest', nargs='?', help='destdir')
    args = parser.parse_args()

    with open(args.config or path.expanduser('~/.github-backup.json'),
              'r') as fi:
        cfg = json.load(fi)

    global USERNAME
    global TOKEN
    global HEADERS
    global DESTDIR
    USERNAME = args.username or cfg.get('username', None)
    TOKEN = cfg['token']
    HEADERS = {'Authorization': 'token '+TOKEN}
    DESTDIR = args.dest or cfg.get('dest')
    now = datetime.datetime.now()
    DESTDIR = path.abspath(path.expanduser(now.strftime(DESTDIR)))

    if cfg.get('zip', True):
        DESTZIP = DESTDIR
        tmpdir = tempfile.TemporaryDirectory()
        DESTDIR = tmpdir.name

    resp = requests.get('https://api.github.com/users/%s/repos' % USERNAME,
                        headers=HEADERS)
    jsondump(USERNAME+'_repos.json', resp.json())
    for repo in resp.json():
        grab_repo(repo)

    if cfg.get('zip', True):
        CURDIR = os.getcwd()
        os.chdir(DESTDIR)
        subprocess.run(['7z', 'a', DESTZIP, "*"])
        os.chdir(CURDIR)


if __name__ == '__main__':
    main()
