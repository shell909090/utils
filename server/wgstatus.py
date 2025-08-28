#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2025-08-20
@author: Shell.Xu
@copyright: 2025, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import sys
import json
import time
import logging
import logging.handlers
import smtplib
import argparse
import subprocess
import configparser
from os import path
from email.mime.text import MIMEText


def setup_logging(lv):
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(lv.upper())


def setup_syslog(addr):
    syslog = logging.getLogger('syslog')
    handler = logging.handlers.SysLogHandler(address=addr)
    handler.setFormatter(logging.Formatter('router wg[%(process)d]: %(message)s'))
    syslog.addHandler(handler)
    return syslog


def run(cmd):
    logging.info(f'run: {cmd}')
    p = subprocess.run(cmd, capture_output=True)
    return p.stdout


def wgshow():
    output = run(['sudo', 'wg', 'show', args.iface]).decode('utf-8')
    status = {}
    for line in output.splitlines():
        line = line.strip()
        if line:
            k, v = line.split(':', 1)
            status[k.strip()] = v.strip()
        else:
            if 'endpoint' in status:
                yield status
            status = {}
    if status and 'endpoint' in status:
        yield status


SECONDS = {'second': 1, 'minute': 60, 'hour': 3600, 'day': 86400}
def cal_time(src):
    st = int(time.time())
    for status in src:
        ago = 0
        for chunk in status['latest handshake'][:-4].split(', '):
            n, suffix = chunk.split(' ', 1)
            ago += int(n)*SECONDS[suffix.rstrip('s')]
        status['ago'] = ago
        status['handshake_timestamp'] = st-ago
        yield status


def filter_new(src, timeout=300):
    for status in src:
        if status['ago'] < timeout:
            yield status


def list2dict(src, name):
    return {status[name]: status for status in src}


def diff_status(cur, his):
    st = int(time.time())
    new = cur.keys() - his.keys()
    timeouted = his.keys() - cur.keys()
    for name in new:
        yield 'user login, name: {peer}, endpoint: {endpoint}, ago: {ago}'.format(**cur[name])
        his[name] = cur[name]
    for name in timeouted:
        status = his[name]
        status['ago'] = (st-status['handshake_timestamp'])
        yield 'user timeout, name: {peer}, endpoint: {endpoint}, ago: {ago}'.format(**status)
        del his[name]


def sendmail(body):
    msg = MIMEText(body)
    msg['From'] = args.sender
    msg['To'] = args.to
    msg['Subject'] = f'wireguard {args.iface} update from router'
    with smtplib.SMTP(host=args.smtp) as smtp:
        smtp.sendmail(args.sender, [args.to], msg.as_string())
    logging.info('mail send out')


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--loglevel', '-l', default='INFO', help='log level')
    parser.add_argument('--iface', '-i', default='wg0', help='wg interface')
    parser.add_argument('--timeout', '-t', type=int, default=300, help='how long will peer timeout')
    parser.add_argument('--db', '-db', default='~/wg/wg0.status.json', help='wg status file')
    parser.add_argument('--printout', '-p', action='store_true', help='print out status and quit')
    parser.add_argument('--syslog', '-sl', help='syslog server')
    parser.add_argument('--smtp', '-s', help='smtp server')
    parser.add_argument('--sender' help='sender email address')
    parser.add_argument('--to', help='receiver email address')
    parser.add_argument('rest', nargs='*', type=str)
    args = parser.parse_args()
    setup_logging(args.loglevel)

    status = filter_new(cal_time(wgshow()), args.timeout)
    status = list2dict(status, 'peer')
    logging.debug('current: %s', json.dumps(status, indent=2))

    if args.printout:
        print(json.dumps(status, indent=2))
        return

    try:
        with open(path.expanduser(args.db)) as fi:
            historial_status = json.load(fi)
    except:
        historial_status = {}
    logging.debug('history: %s', json.dumps(historial_status, indent=2))

    diff = list(diff_status(status, historial_status))
    if not diff:
        logging.info('no change, quit.')
        return

    for msg in diff:
        logging.warning(msg)

    if args.syslog:
        syslog = setup_syslog((args.syslog, 514))
        for msg in diff:
            syslog.info(msg)

    if args.smtp:
        sendmail('\n'.join(diff))

    with open(path.expanduser(args.db), 'w') as fo:
        json.dump(historial_status, fo, indent=2)
    logging.info(f'update db: {args.db}')


if __name__ == '__main__':
    main()
