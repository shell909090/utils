#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2022-01-02
@author: Shell.Xu
@copyright: 2022, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
@comment:
  数据源直接浏览：http://bmfw.www.gov.cn/yqfxdjcx/risk.html
'''
import sys
import json
import time
import hashlib

import requests


def sha256sum(s):
    h = hashlib.sha256()
    h.update(s.encode('utf-8'))
    return h.hexdigest().upper()


def yqfxdjcx():
    url = 'http://103.66.32.242:8005/zwfwMovePortal/interface/interfaceJson'
    timestamp = str(int(time.time()))

    wif_nonce = 'QkjjtiLM2dCratiA'
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'x-wif-nonce': wif_nonce,
        'x-wif-paasid': 'smt-application',
        'x-wif-signature': sha256sum(f'{timestamp}fTN2pfuisxTavbTuYVSsNJHetwq5bJvC{wif_nonce}{timestamp}'),
        'x-wif-timestamp': timestamp,
    }

    nonce = '123456789abcdefg'
    body = {
        'appId': 'NcApplication',
        'paasHeader': 'zdww',
        'timestampHeader': timestamp,
        'nonceHeader': nonce,
        'signatureHeader': sha256sum(f'{timestamp}23y0ufFl5YxIyGrI8hWRUZmKkvtSjLQA{nonce}{timestamp}'),
        'key': '3C502C97ABDA40D0A60FBEE50FAAD1DA',
    }

    resp = requests.post(url, headers=headers, data=json.dumps(body))
    if resp.status_code != 200:
        raise Exception(f'http code error: {resp.status_code}')
    data = resp.json()
    if data['code'] != 0:
        raise Exception(f'json error: {data["msg"]}')
    return data['data']


def list2set(l):
    return {(o['province'], o['city'], o['county']) for o in l}, \
        {(o['province'], o['city'], o['county']): len(o['communitys']) for o in l}


def print_tree(l, nums):
    last = None
    for o in l:
        o1 = o
        if last is not None:
            o1 = tuple((i if i != i0 else '  ' * len(i) for i, i0 in zip(o, last)))
        print(' '.join(o1), nums[o])
        last = o


def main():
    import pprint

    data = yqfxdjcx()
    # pprint.pprint(data)

    highset, highnum = list2set(data['highlist'])
    middleset, middlenum = list2set(data['middlelist'])
    # middleset = middleset - highset

    print(data['end_update_time'])
    print('high:')
    print_tree(sorted(highset), highnum)
    print('middle:')
    print_tree(sorted(middleset), middlenum)


if __name__ == '__main__':
    main()
