#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-10-23
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import gevent
from gevent import pool, monkey
monkey.patch_all()

import dbm
import sys
import json
import argparse

import nvdlib


def query_cve(db, cve):
    if cve not in db:
        rs = nvdlib.searchCVE(cveId=cve)
        if not rs:
            return
        s = rs[0].score
        db[cve] = json.dumps(s)
    else:
        s = json.loads(db[cve])
    if not s[1]:
        return
    if s[1] < args.minimum_score:
        return
    print(cve)
    print(s)
    print(f'https://security-tracker.debian.org/tracker/{cve}')
    print('------')


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--cve-db', '-c', default='cve.db')
    parser.add_argument('--pool-size', '-p', type=int, default=1)
    parser.add_argument('--minimum-score', '-m', type=float, default=7.5)
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    cve_list = set()
    if not args.rest:
        for line in sys.stdin.readlines():
            cve_list.add(line.strip())
    else:
        for fp in args.rest:
            with open(fp) as fi:
                for line in fi.readlines():
                    cve_list.add(line.strip())

    p = pool.Pool(args.pool_size)
    with dbm.open(args.cve_db, 'c') as db:
        for cve in cve_list:
            p.spawn(query_cve, db, cve)
        p.join()


if __name__ == '__main__':
    main()
