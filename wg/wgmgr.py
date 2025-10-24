#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2020-05-11
@author: Shell.Xu
@copyright: 2020, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import sys
import json
import getopt
import argparse
import configparser


def fmt_data(name, data, comment=None):
    return f'[{name}]\n%s\n' % '\n'.join([f'{k} = {v}' for k, v in data.items()])


def copy_in_case(peer, name1, pcfg, name2):
    if pcfg.get(name2):
        peer[name1] = pcfg[name2]


def translate_ips(ips):
    for c in ips.split(','):
        c = c.strip()
        if ':' in c:
            yield c+'/128'
        elif '.' in c:
            yield c+'/32'


def gen_peer(cfg, name):
    pcfg = dict(cfg[name])
    conf = []

    iface = {
        'PrivateKey': pcfg['private'],
        'ListenPort': pcfg['port'],
    }
    copy_in_case(iface, 'Address', pcfg, 'address')
    copy_in_case(iface, 'DNS', pcfg, 'dns')
    copy_in_case(iface, 'MTU', pcfg, 'mtu')
    copy_in_case(iface, 'PostUp', pcfg, 'postup')
    copy_in_case(iface, 'PostDown', pcfg, 'postdown')
    conf.append(fmt_data('Interface', iface))

    for pname in cfg.sections():
        if pname == name:
            continue
        pcfg = dict(cfg[pname])
        if not args.all and not pcfg.get('host'):
            continue
        if pcfg.get('disable'):
            continue

        peer = {
            'PublicKey': pcfg['public']
        }
        if pcfg.get('host'):
            peer['Endpoint'] = f'{pcfg["host"]}:{pcfg["port"]}'
        cidrs = []
        if pcfg.get('address'):
            cidrs.append(','.join(translate_ips(pcfg['address'])))
        if pcfg.get('net'):
            cidrs.append(pcfg['net'])
        if cidrs:
            peer['AllowedIPs'] = ','.join(cidrs)
        copy_in_case(peer, 'PersistentKeepalive', pcfg, 'keepalive')
        conf.append(fmt_data('Peer', peer))

    return '\n'.join(conf)


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', '-a', action='store_true')
    parser.add_argument('--list', '-l', action='store_true')
    parser.add_argument('--json-map', '-jm', action='store_true')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.read(args.rest[0])

    if args.list:
        print('\n'.join([name for name in cfg]))
        return

    if args.json_map:
        json_map = {cfg[name]['public']: name for name in cfg if 'public' in cfg[name]}
        print(json.dumps(json_map, indent=2))
        return

    peer = args.rest[1]
    if peer in cfg.sections():
        print(gen_peer(cfg, peer))


if __name__ == '__main__':
    main()
