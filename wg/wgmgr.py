#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2020-05-11
@author: Shell.Xu
@copyright: 2020, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import sys
import getopt
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
    pcfg = dict(cfg.items(name))
    conf = []

    iface = {
        'PrivateKey': pcfg['private'],
        'ListenPort': pcfg['port'],
    }
    copy_in_case(iface, 'Address', pcfg, 'address')
    copy_in_case(iface, 'DNS', pcfg, 'dns')
    conf.append(fmt_data('Interface', iface))

    for pname in cfg.sections():
        if pname == name:
            continue
        pcfg = dict(cfg.items(pname))
        if '-a' not in optdict and not pcfg.get('host'):
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
    ''' wgmgr list/[config name] '''

    global optdict
    optlist, args = getopt.getopt(sys.argv[1:], 'ah')
    optdict = dict(optlist)
    if '-h' in optdict:
        print(main.__doc__)
        return

    if len(args) < 2:
        print(main.__doc__)

    cfg = configparser.ConfigParser()
    cfg.read(args[0])

    cmd = args[1]
    if cmd == 'list':
        print('\n'.join([name for name in cfg.sections()]))
    elif cmd in cfg.sections():
        print(gen_peer(cfg, cmd))
    else:
        print(main.__doc__)


if __name__ == '__main__':
    main()
