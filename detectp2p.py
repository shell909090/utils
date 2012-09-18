#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2012-09-18
@author: shell.xu
'''
import os, sys, time, socket, getopt, logging
from os import path
import dpkt, pcap

def get_netaddr(ip, mask):
    return ''.join(map(lambda x, y: chr(ord(x) & ord(y)), ip, mask))

def ipfilter(ip):
    src = get_netaddr(ip.src, optdict['-m']) == optdict['netaddr']
    dst = get_netaddr(ip.dst, optdict['-m']) == optdict['netaddr']
    if src and dst: return None
    elif src: return ip.src
    elif dst: return ip.dst
    else: return None

class IpStatus(object):
    def __init__(self, ipaddr):
        self.ipaddr = ipaddr
        self.tcps, self.udps = {}, {}

    def add(self, eth):
        ip = eth.data
        if hasattr(ip, 'tcp'):
            self.addsome(eth, ip, self.tcps)
        else: self.addsome(eth, ip, self.udps)

    def addsome(self, eth, ip, d):
        p = ip.data
        if ip.src == self.ipaddr:
            dst = (ip.dst, p.dport)
        else: dst = (ip.src, p.sport)
        d.setdefault(dst, [0, 0])
        if ip.src == self.ipaddr:
            d[dst][0] += len(eth)
        else: d[dst][1] += len(eth)

    def detect(self, s):
        print >>s, 'ipaddr: %s' % socket.inet_ntoa(self.ipaddr)
        self.detectsome(s, self.tcps, 'tcp')
        self.detectsome(s, self.udps, 'udp')

    def detectsome(self, s, p, type):
        for k, v in p.iteritems():
            if k[1] < optdict['-s']: continue
            print >>s, '\t%s:%d (%s) : sent %d, recved %d' % (
                socket.inet_ntoa(k[0]), k[1], type, v[0], v[1])

def analyze(s):
    ips = {}
    pc = pcap.pcap(optdict['-i'])
    proto = 'tcp'
    if '-u' in optdict: proto += ' or udp'
    pc.setfilter(proto)
    t = time.time()

    try:
        for ts, pkt in pc:
            eth = dpkt.ethernet.Ethernet(pkt)
            if hasattr(eth, 'ip6'): continue
            ip = eth.data
            logging.info('%s:%d -> %s:%d' % (
                    socket.inet_ntoa(ip.src), ip.data.dport,
                    socket.inet_ntoa(ip.dst), ip.data.sport))
            inaddr = ipfilter(ip)
            if inaddr is None: continue
            ips.setdefault(inaddr, IpStatus(inaddr))
            ips[inaddr].add(eth)

            if optdict['-k'] and time.time() - t > optdict['-k']: break
    except KeyboardInterrupt: pass

    for v in ips.values(): v.detect(s)
    s.flush()

def main():
    '''
    -h: help
    -i: iface, eth0 as default
    -k: keep time and quit, 30 as default, use 0 for forever run
    -n: network, 192.168.0.0 as default
    -m: netmask, 255.255.0.0 as default
    -s: system port range, 1024 as default
    -u: with udp
    '''
    global optdict
    optlist, args = getopt.getopt(sys.argv[1:], 'hi:k:n:m:s:u')
    optdict = dict(optlist)
    if '-h' in optdict:
        exe = path.basename(sys.argv[0])
        print '%s [-h] [-k keep time] [-i iface] [-u]' % exe
        print main.__doc__
        return

    optdict.setdefault('-i', 'eth0')
    optdict.setdefault('-k', '30')
    optdict.setdefault('-n', '192.168.0.0')
    optdict.setdefault('-m', '255.255.0.0')
    optdict.setdefault('-s', '1024')

    optdict['-k'] = int(optdict['-k'])
    optdict['-n'] = socket.inet_aton(optdict['-n'])
    optdict['-m'] = socket.inet_aton(optdict['-m'])
    optdict['netaddr'] = get_netaddr(optdict['-n'], optdict['-m'])
    optdict['-s'] = int(optdict['-s'])

    analyze(sys.stdout)

if __name__ == '__main__': main()
