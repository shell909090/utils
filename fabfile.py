#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2015-08-13
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from fabric.api import env, sudo, run, get, put, task, hide, settings


env.use_ssh_config = True
env.roledefs['debox'] = ['srv', 'web', 'pub', 'docker', 'debox', 'router']
env.roledefs['vps'] = ['vlt1', 'auus1']


@task
def upgrade():
    sudo('aptitude -q=2 update')
    sudo('aptitude -y full-upgrade')
    sudo('aptitude clean')
    sudo('aptitude forget-new')


@task
def pubkey():
    pubkeys = [
        'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIANXSjD8YRhbmqr5tyjwQIRnqi4BMGY2CPbiGf/3EvWf shell@201602',
        'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJMb4giDpPuVu0qi6YT9KhoK/dIidy6TE4OlocuchWFR mobile@201602'
    ]

    run('mkdir -p ~/.ssh/')
    run('chmod 700 ~/.ssh')
    run('touch ~/.ssh/authorized_keys')
    run('chmod 600 ~/.ssh/authorized_keys')

    for key in pubkeys:
        with settings(warn_only=True):
            r = run('grep "%s" ~/.ssh/authorized_keys' % key)
            if r.succeeded:
                continue
        run('echo "%s" >> ~/.ssh/authorized_keys' % key)
