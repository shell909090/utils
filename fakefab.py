#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2016-10-22
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from __future__ import absolute_import, division,\
    print_function, unicode_literals
import sys
import tempfile
import subprocess
from os import path
from contextlib import contextmanager


if sys.version_info.major == 3:
    unicode = str
else:
    bytes = str


class FakeEnv(object):

    def __init__(self):
        self.roledefs = {}


env = FakeEnv()


class Result(object):

    def __init__(self):
        self.succeeded = True
        self.value = ''

    def __str__(self):
        return bytes(self.value)

    def __unicode__(self):
        return unicode(self.value)

    def splitlines(self):
        return self.value.splitlines()


def run(s, stdout=None):
    r = Result()
    try:
        r.value = subprocess.check_output(s, shell=True)
    except subprocess.CalledProcessError as err:
        r.succeeded = False
        r.value = str(err)
    else:
        r.succeeded = True
    return r


def sudo(s):
    return run('sudo bash -c "%s"' % s)


def get(src, dst, use_sudo=False):
    src = path.expanduser(src)
    if hasattr(dst, 'write'):
        data = (sudo if use_sudo else run)('cat "%s"' % src)
        dst.write(data)
        dst.flush()
        return
    dst = path.expanduser(dst)
    return (sudo if use_sudo else run)('cp "%s" "%s"' % (src, dst))


def put(src, dst, use_sudo=False):
    dst = path.expanduser(dst)
    f = sudo if use_sudo else run
    if hasattr(src, 'read'):
        with tempfile.NamedTemporaryFile() as fo:
            fo.write(src.read())
            fo.flush()
            r = f('cp "%s" "%s"' % (fo.name, dst))
            f('chown root.root "%s"' % dst)
            return r
    src = path.expanduser(src)
    return f('cp "%s" "%s"' % (src, dst))


tasks = {}


def task(f):
    tasks[f.__name__] = f
    return f


@contextmanager
def settings(**kw):
    yield


@contextmanager
def hide(*p):
    yield
