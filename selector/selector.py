#!env python3
# -*- coding: utf-8 -*-
'''
@date: 2019-03-08
@author: Shell.Xu
@copyright: 2019, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import sys


def search(exps, numbers=False):
    if not exps:
        return
    exps = exps.split('.')

    def _search(obj):
        stk = [(exps, obj)]
        while stk:
            exp, obj = stk.pop(-1)
            if not exp:
                yield obj
                continue
            e0 = exp[0]
            if e0 == '?':
                e1 = exp[1:]
                if hasattr(obj, '__iter__'):
                    stk += [(e1, o) for o in reversed(obj)]
                elif hasattr(obj, 'items'):
                    stk += [(e1, v) for k, v in obj.items()]
            elif e0 == '*':
                if hasattr(obj, '__iter__'):
                    stk += [(exp, o) for o in reversed(obj)]
                elif hasattr(obj, 'items'):
                    e1, e2 = exp[1], exp[2:]
                    stk += [(e2, v) if k == e1 else (exp, v)
                              for k, v in obj.items()]
            else:
                e1 = exp[1:]
                # performance difference (with/wo numbers)
                # 2.51 ms ± 17 µs per loop
                # 3.4 ms ± 67.9 µs per loop
                if numbers:
                    try:
                        stk.append((e1, obj[int(e0)]))
                    except:
                        pass
                try:
                    stk.append((e1, obj[e0]))
                except:
                    pass

    return _search


def inputs(d, fmts):
    for fmt in fmts:
        if fmt == 'json':
            try:
                return __import__("json").loads(d)
            except:
                pass
        elif fmt == 'yaml':
            try:
                return __import__("yaml").load(d)
            except:
                pass
        elif fmt == 'eval':
            try:
                return eval(d)
            except:
                pass
        else:
            raise Exception('unknown format %s' % fmt)


def outputs(obj, fmt):
    if fmt == 'json':
        print(__import__("json").dumps(obj, indent=2))
    elif fmt == 'yaml':
        print(__import__("yaml").safe_dump(obj))
    elif fmt == 'pprint':
        import pprint
        pprint.pprint(obj)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--format', default='json,yaml',
        help='input format, could be {json,yaml,eval}. "json,yaml" by default.')
    parser.add_argument(
        '-s', '--search', help='search expression.')
    parser.add_argument(
        '-o', '--output', default='json',
        help='output format, could be {json,yaml,pprint}.')
    parser.add_argument('file', nargs='*')
    args = parser.parse_args()

    s = search(args.search)
    fmts = args.format.split(',')
    def io_search(d):
        obj = inputs(d, fmts)
        if s:
            obj = list(s(obj))
        outputs(obj, args.output)

    if not args.file:
        io_search(sys.stdin.read())
    else:
        for fn in args.file:
            with open(fn, 'rb') as fi:
                d = fi.read()
            io_search(d)


if __name__ == '__main__':
    main()
