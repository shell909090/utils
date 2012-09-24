#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2012-09-24
@author: shell.xu
@remark: 用于系统启动/停止/管理的一些简单函数
@license:
  Copyright (c) 2012 Shell Xu
  All rights reserved.

  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

  Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
import os, sys, time, signal, logging
from os import path
from contextlib import contextmanager

def import_config(*cfgs):
    d = {}
    for cfg in reversed(cfgs):
        try:
            with open(path.expanduser(cfg)) as fi:
                eval(compile(fi.read(), cfg, 'exec'), d)
        except (OSError, IOError): pass
    return dict([(k, v) for k, v in d.iteritems() if not k.startswith('_')])

def initlog(lv, logfile=None):
    rootlog = logging.getLogger()
    if logfile: handler = logging.FileHandler(logfile)
    else: handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s,%(msecs)03d %(process)d %(name)s[%(levelname)s]: %(message)s',
            '%H:%M:%S'))
    rootlog.addHandler(handler)
    rootlog.setLevel(lv)

logger = logging.getLogger('service')

def daemonized(closefds=True):
    try:
        pid = os.fork()
        if pid > 0: return pid
    except OSError, e: sys.exit(1)
    os.chdir("/")
    os.setsid()
    os.umask(0)
    if closefds:
        for i in xrange(0, 3): os.close(i)
    try:
        if os.fork() > 0: sys.exit(0)
    except OSError, e: sys.exit(1)
    logger.info('daemoniz finished, new pid %d' % os.getpid())
    return 0

def get_pid_status(pid):
    try: os.getsid(pid)
    except OSError: return False
    return True

def kill_stand(pids, timeout):
    if not pids: return
    t_start = time.time()
    logger.debug('try term %s.' % str(pids))
    for pid in pids:
        try: os.kill(pid, signal.SIGTERM)
        except OSError: pass
    while (time.time() - t_start) < timeout and pids:
        pids = [pid for pid in pids if get_pid_status(pid)]
        time.sleep(1)
    logger.debug('try kill %s.' % str(pids))
    for pid in pids:
        try: os.kill(pid, signal.SIGKILL)
        except OSError: pass

@contextmanager
def lockfile(filename, share=False):
    logger.debug('locking %s' % filename)
    f = open(filename, 'r')
    fcntl.flock(f.fileno(), fcntl.LOCK_SH if share else fcntl.LOCK_EX)
    try: yield f
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()
        logger.debug('unlock %s' % filename)

class RunfileNotExistError(StandardError): pass
class RunfileExistError(StandardError): pass

class RunFile(object):
    ERR_NOTEXIST = '%s not exist, daemon not started yet.'
    ERR_EXIST = '%s is exists.\nIf you really wanna run daemon, remove it first.'

    def __init__(self, filename): self.bind(filename)
    def bind(self, filename): self.filename = filename

    def chk_state(self, in_run):
        b = path.exists(self.filename)
        if in_run and not b:
            raise RunfileNotExistError(self.ERR_NOTEXIST % self.filename)
        elif not in_run and b:
            raise RunfileExistError(self.ERR_EXIST % self.filename)

    def update(self, content):
        with open(self.filename, 'w') as fo: fo.write(content)

    def getpids(self):
        self.chk_state(True)
        with open(self.filename, 'r') as f:
            return [int(line.strip()) for line in f]

    def kill(self, sig):
        for pid in self.getpids(): os.kill(pid, sig)

    def kill_stand(self, timeout=5):
        kill_stand(self.getpids(), timeout)

    def getstatus(self):
        return all(map(get_pid_status, self.getpids()))

    def acquire(self):
        self.chk_state(False)
        self.update(str(os.getpid()))

    def release(self):
        self.chk_state(True)
        os.remove(self.filename)

    def __enter__(self): self.acquire()

    def __exit__(self, type, value, traceback): self.release()

class Service(object):
    def __init__(self, name, *cfgs):
        self.name = name
        self.config = {}
        if cfgs: self.config.update(import_config(*cfgs))
        initlog(getattr(logging, self.config.get('loglevel', 'WARNING')),
                self.config.get('logfile', None))
        self.runfile = RunFile(self.config.get('pidfile', '/var/run/%s.pid' % self.name))

    def handler(self, cmds):
        try: 
            if not cmds: self.on_help()
            elif not hasattr(self, 'on_%s' % cmds[0].lower()):
                raise Exception('command not found')
            else: getattr(self, 'on_%s' % cmds[0].lower())()
        finally: self.final()

    def final(self): pass

    def on_help(self):
        cmds = [n[3:] for n in dir(self) if n.startswith('on_')]
        print '%s {%s}' % (sys.argv[0], '|'.join(cmds))

    def on_restart(self):
        self.on_stop()
        self.on_start()

    def on_stop(self):
        try: self.runfile.kill_stand()
        except RunfileNotExistError:
            logger.error('run file not found.')
        try: self.runfile.release()
        except RunfileNotExistError: pass
        logger.info('%s stoped.' % self.name)
        print >>sys.stderr, '%s stoped.' % self.name

    def on_start(self):
        if not self.config.get('daemon', False):
            logger.info('not start due to config.daemon not set')
            return
        try: self.runfile.chk_state(False)
        except RunfileExistError:
            print >>sys.stderr, '%s already started.' % self.name
            return
        pid = daemonized()
        if pid > 0:
            logger.info('%s starting' % self.name)
            print >>sys.stderr, '%s starting, pid %d' % (self.name, pid)
            return
        try:
            with self.runfile:
                try: self.run()
                except Exception, err: logger.exception(err)
        except Exception, err: logger.exception(err)

def watcher(*runners):
    pids = dict([(runner, 0) for runner in runners])
    def cleanup(signum, frame):
        if signum != signal.SIGTERM: return
        logger.info('signal TERM, start to stop childs')
        tokill = pids.values()
        pids.clear()
        kill_stand(tokill, 3)
    signal.signal(signal.SIGTERM, cleanup)
    while pids:
        for runner, pid in pids.iteritems():
            if pid and get_pid_status(pid): continue
            pids[runner] = runner(pid)
        time.sleep(1)
        try: os.wait()
        except OSError: continue
    logger.info('system exit')

class WatchService(Service):

    def __init__(self, name, runners, *cfgs):
        self.runners = runners
        super(WatchService, self).__init__(name, *cfgs)

    def run(self): watcher(*self.runners)
