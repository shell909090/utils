#!env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
import argparse

from os import path

import yaml
from jinja2 import Environment, FileSystemLoader


def render(src, dst):
    if not src:
        tmpl = env.from_string(sys.stdin.read())
    else:
        tmpl = env.get_template(src)

    d = tmpl.render(vars)

    if not dst:
        sys.stdout.write(d)
        return

    pathname = path.dirname(dst)
    if pathname and not path.exists(pathname):
        os.makedirs(pathname)

    with open(dst, 'w') as fo:
        fo.write(d)

    if src and dst and src != dst:
        shutil.copymode(src, dst)


def load_datafile(d):
    try:
        vars.update(yaml.safe_load(d))
    except:
        pass
    else:
        return
    try:
        vars.update(json.loads(d))
    except:
        pass
    else:
        return
    raise Exception(f'unknown data file {d}')


def main(args):
    global env
    global vars
    env = Environment(loader=FileSystemLoader(args.workdir))
    env.trim_blocks = True
    vars = {
        'whoami': os.getlogin,
    }
    vars.update(os.environ)

    if args.datafile:
        for fn in args.datafile:
            if fn == '-':
                load_datafile(sys.stdin.read())
                continue
            if not path.isfile(fn):
                sys.stderr.write('%s not exists\n' % fn)
                continue
            with open(fn) as fi:
                load_datafile(fi.read())

    if args.variable:
        for e in args.variable:
            if '=' not in e:
                sys.stderr.write('unknown variable %s\n' % e)
                continue
            k, v = e.split('=', 1)
            vars[k.strip()] = v.strip()

    if args.imports:
        for fn in args.imports:
            if not path.isfile(fn):
                sys.stderr.write('%s not exists\n' % fn)
                continue
            with open(fn) as fi:
                eval(compile(fi.read(), path.basename(fn), 'exec'), vars)

    if not args.recursion:
        render(args.src, args.dst)
        return

    for root, dirs, files in os.walk(args.src):
        for fn in files:
            srcpath = path.join(root, fn)
            relpath = path.relpath(srcpath, args.src)
            dstpath = path.join(args.dst, relpath)
            print("%s => %s" % (srcpath, dstpath))
            render(srcpath, dstpath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-w', '--workdir', default='.')
    parser.add_argument(
        '-r', '--recursion', action='store_true')
    parser.add_argument(
        '-e', '--variable', action='append')
    parser.add_argument(
        '-f', '--datafile', action='append')
    parser.add_argument(
        '-i', '--imports', action='append')
    parser.add_argument('src', nargs='?')
    parser.add_argument('dst', nargs='?')
    main(parser.parse_args())
