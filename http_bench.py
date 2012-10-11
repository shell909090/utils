#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2012-09-30
@author: shell.xu
'''
import os, re, sys, time, getopt, subprocess
from contextlib import contextmanager

def read_table(s):
    for line in s:
        if line.startswith(' ') or line.startswith('WARNING:'): continue
        try: name, dt = line.strip().split(':', 1)
        except ValueError: break
        d = dt.split()
        yield name.lower(), (d[1], d[0], d[4])

dmap = {
    'rps': re.compile('Requests per second:\s*([\d\.]+) \[.*\] \(mean\)'),
    'tpr': re.compile('Time per request:\s*([\d\.]+) \[.*\] \(mean, across all concurrent requests\)'),
    'tr': re.compile('Transfer rate:\s*([\d\.]+) \[.*\] received')}
re_header = re.compile('([\d.]+) \[.*\] (.*)')
def run_ab(url, c, n):
    p = subprocess.Popen(['ab', '-c', str(c), '-n', str(n), url],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    r = {}
    for line in p.stdout:
        for k, v in dmap.iteritems():
            if line.startswith('Connection Times'):
                for k, v in read_table(p.stdout): yield k, v
                return
            m =v.match(line.strip())
            if m is None: continue
            yield k, [m.group(1),]

def run_test(f, url, minc=50, maxc=1000, interval=None,
             times=10, minn=5000, maxn=20000):
    if interval is None: interval = minc
    r = {}
    for c in xrange(minc, maxc, interval):
        print 'concurrency: %d' % c
        for name, value in f(url, c, max(c*times, minn)):
            r.setdefault(name, [])
            try: r[name].append([c,] + map(float, value))
            except:
                print name, value
                raise
        time.sleep(1)
    return r

class Gnuplot(object):
    def __init__(self, filename, x=1440, y=900):
        self.cmds = ['set terminal png large size %d, %d' % (x, y),
                     'set output "%s"' % filename,]

    def cmd(self, cmd):
        self.cmds.extend(cmd.split('\n'))

    def data(self, d):
        for i in d: self.cmd(' '.join(map(str, i)))
        self.cmd('e')

    @contextmanager
    def multiplot(self, x, y):
        self.cmd('set multiplot layout %d, %d' % (x, y))
        try: yield
        finally: self.cmd('unset multiplot')

    def set(self, k, v=None):
        if v is None: self.cmd('set %s' % k)
        else: self.cmd('set %s "%s"' % (k, v))

    def unset(self, k): self.cmd('unset %s' % k)

    @contextmanager
    def withset(self, k, v=None):
        self.set(k, v)
        try: yield
        finally: self.unset(k)

    def showcmds(self):
        print '\n'.join(self.cmds)

    def run(self):
        p = subprocess.Popen(['gnuplot',], stdin=subprocess.PIPE)
        p.stdin.write('\n'.join(self.cmds))
        p.stdin.close()
        p.wait()

infod = {'rps': 'request per second',
         'tpr': 'time per request(ms)',
         'tr': 'data per second(MB/s)'}
src = ['connect', 'processing', 'waiting', 'total']
def show(dt, outfile):
    g = Gnuplot(outfile)

    with g.multiplot(3, 2):

        g.set('title', 'performance')
        g.set('xlabel', 'Concurrency')
        g.set('ylabel', infod['rps'])
        with g.withset('y2label', infod['tr']):
            with g.withset('y2tics'):
                g.cmd('plot "-" with linespoints title "%s" axes x1y1,\
 "-" with linespoints title "%s" axes x1y2' % ('rps', 'tr'))
                g.data(dt['rps'])
                g.data(dt['tr'])

        g.set('title', 'time')
        g.set('xlabel', 'Concurrency')
        g.set('ylabel', infod['tpr'])
        g.cmd('plot "-" with linespoints title "tpr"')
        g.data(dt['tpr'])

        for n in src:
            g.set('title', 'time')
            g.set('xlabel', 'Concurrency')
            g.set('ylabel', infod['tpr'])
            g.cmd('plot "-" with yerrorlines title "%s"' % n)
            g.data(dt[n])

    return g

def main():
    '''
    -h: help
    -i: interval
    -m: min concurrency
    -M: max concurrency
    -o: output filename
    '''
    optlist, args = getopt.getopt(sys.argv[1:], 'himMo')
    optdict = dict(optlist)
    if '-h' in optdict:
        print '%s [-h] [-i interval] [-m min] [-M max] [-o output filename] url' % sys.argv[0]
        print main.__doc__
        return
    dt = run_test(run_ab, args[0], minc=optdict.get('-m', 50),
                  maxc=optdict.get('-M', 1000), interval=optdict.get('-i', None))
    show(dt, optdict.get('-o', 'output.png')).run()
    os.system('display output.png')

if __name__ == '__main__': main()
