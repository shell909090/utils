#!/usr/bin/python
# -*- coding: utf-8 -*-
### BEGIN INIT INFO
# Provides:          tester
# Required-Start:    $network $local_fs $remote_fs
# Required-Stop:     $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start and stop sshtunnel client daemon
### END INIT INFO

# Author: Shell Xu <shell909090@gmail.com>
'''
@date: 2012-09-27
@author: shell.xu
'''
import os, sys, time, signal, logging
import service

logger = logging.getLogger('init.d')

def sleeper():
    while True:
        time.sleep(1)

def sleeper_runner(orig_pid):
    pid = os.fork()
    if pid > 0:
        logger.debug('create new pid ' + str(pid))
        return pid
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    try: sleeper()
    finally: os.exit(0)

def main():
    srv = service.WatchService('tester', [sleeper_runner,], 'tester.cfg')
    srv.handler(sys.argv[1:])

if __name__ == '__main__': main()
