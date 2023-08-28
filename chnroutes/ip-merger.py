#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2023-08-28
@author: Shell.Xu
@copyright: 2023, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import sys
import ipaddress


def merge(src):
    dst = []
    for cidr in src:
        while dst:
            if cidr.subnet_of(dst[-1]):
                # if cidr is subnet of tail, or cidr equal to the tail.
                break
            elif cidr.supernet_of(dst[-1]):
                dst[-1] = cidr
                break
            elif cidr.supernet() == dst[-1].supernet():
                cidr = dst.pop(-1).supernet()
            else:
                dst.append(cidr)
                break
        else:
            dst.append(cidr)
    return dst


def main():
    cidrs = [ipaddress.ip_network(line.strip(), strict=False) for line in sys.stdin]
    for cidr in merge(sorted(cidrs)):
        print(cidr)


if __name__ == '__main__':
    main()
