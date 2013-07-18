#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-07-18
@author: shell.xu
@license:
    Copyright (C) 2013 Shell Xu

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os, sys, stat
from cStringIO import StringIO
from fabric import api, operations
from fabric.contrib import files

def rewrite(filepath, context, target, use_sudo=False):
    if files.contains(filepath, context):
        files.sed(filepath, '^.*%s.*$' % context, target, use_sudo=use_sudo)
    else: files.append(filepath, target, use_sudo=use_sudo)

def sudo(username='shell'):
    ''' sudo username to setup user can sudo to root '''
    api.run('aptitude install sudo')
    operations.put(
        StringIO('%s   ALL=(ALL) NOPASSWD: ALL' % username),
        '/etc/sudoers.d/%s' % username, mode=stat.S_IRUSR)

def superuser(username='shell'):
    ''' create a superuser to ssh login and run sudo '''
    api.run('adduser --quiet %s' % username)
    sudo(username)

debian_release = 'jessie'
apt_src = [
    'http://mirrors.ustc.edu.cn/debian/',
    'http://mirrors.yun-idc.com/debian/',
    'http://localhost:9999/debian/',
    'http://192.168.5.68:9999/debian/',
    'http://srv/debian/']
def apt_source():
    ''' auto setup apt source '''
    f = files.first('/etc/apt/sources.list', '/etc/apt/sources.list.d/debian.list')
    for i, l in enumerate(apt_src): print i + 1, l
    chooses = [int(i.strip()) for i in operations.prompt('choose> ').split(',')]
    s = ['deb %s %s main contrib non-free' % (l.strip(), debian_release)
         for i, l in enumerate(apt_src) if i+1 in chooses]
    operations.put(
        StringIO('# from fab init.py\n' + '\n'.join(s)),
        f, use_sudo=True)
    api.sudo('aptitude update')

def apt_install():
    ''' auto install packages '''
    pkgs = ['less', 'vim', 'mtr-tiny', 'sysv-rc-conf', 'ifstat', 'iftop', 'sysv-rc-conf']
    api.sudo('aptitude install %s' % ' '.join(pkgs))

def sshd_config():
    # api.sudo('aptitude install denyhosts')
    sshd_config = '/etc/ssh/sshd_config'
    rewrite(sshd_config, 'PasswordAuthentication', 'PasswordAuthentication no', use_sudo=True)
    rewrite(sshd_config, 'PermitRootLogin', 'PermitRootLogin no', use_sudo=True)
    rewrite(sshd_config, 'UseDNS', 'UseDNS no', use_sudo=True)

def sshd_hostkey():
    ''' reset host key of ssh server '''
    api.sudo('rm -f /etc/ssh/*host*')
    api.sudo('dpkg-reconfigure openssh-server')

def ipXtables(name, cmd, tgtfile, fakemode=False):
    accept_ports = operations.prompt('accept ports for %s (split by semicomma) [22]: ' % name)
    if not accept_ports: accept_ports = '22'
    if not fakemode: do = api.sudo
    else: do = lambda x: sys.stdout.write(x+'\n')

    do('/etc/init.d/iptables-persistent flush')
    do('%s -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT' % cmd)
    do('%s -A INPUT -i lo -j ACCEPT' % cmd)
    for p in accept_ports.split(';'):
        if '-' in p or ',' in p:
            do('%s -A INPUT -p tcp -m multiport --dports %s -j ACCEPT' % (cmd, p))
        else: do('%s -A INPUT -p tcp -m tcp --dport %s -j ACCEPT' % (cmd, p))
    do('%s -P INPUT DROP' % cmd)
    if not fakemode: do('%s-save > %s' % (cmd, tgtfile))
    do('/etc/init.d/iptables-persistent restart')

def iptables():
    ''' auto setup iptables, use -p to print out. '''
    api.sudo('aptitude install iptables-persistent')
    ipXtables('ipv4', 'iptables', '/etc/iptables/rules.v4')

def ip6tables():
    ''' auto setup iptables, use -p to print out. '''
    api.sudo('aptitude install iptables-persistent')
    ipXtables('ipv6', 'ip6tables', '/etc/iptables/rules.v6')

def sysctl():
    ''' setup sysctl. '''
    operations.put(
        StringIO('net.ipv4.tcp_congestion_control = htcp'),
        '/etc/sysctl.d/net.conf', use_sudo=True)
    api.sudo('sysctl -p /etc/sysctl.d/net.conf')

# TODO:
def service():
    ''' setup system services. '''
    os.system('sysv-rc-conf')
    os.system('dpkg-reconfigure locales')
    os.system('dpkg-reconfigure tzdata')

def shelllink():
    ''' line /bin/sh to bash '''
    api.sudo('ln -sf bash /bin/sh')

def system_config():
    ''' config system '''
    apt_source()
    apt_install()
    sshd_config()
    iptables()
    ip6tables()
    sysctl()
    shelllink()

def bashrc(name='shell909090', email='shell909090@gmail.com', editor='vim'):
    ''' setup user environment. '''
    user_config = '.bashrc'
    rewrite(user_config, 'DEBFULLNAME', 'export DEBFULLNAME="%s"' % name)
    rewrite(user_config, 'DEBEMAIL', 'export DEBEMAIL=%s' % email)
    rewrite(user_config, 'EDITOR', 'export EDITOR=%s' % editor)

def ssh_config():
    ''' setup ssh client config '''
    ssh_config = '.ssh/config'
    ans1 = operations.prompt('will you use ControlMaster[no]? ')
    if not ans1: ans1 = 'no'
    if ans1.lower().startswith('y'):
        rewrite(ssh_config, 'ControlMaster', 'ControlMaster\t\tauto')
        rewrite(ssh_config, 'ControlPath', 'ControlPath\t\t/tmp/ssh_mux_%h_%p_%r')
        rewrite(ssh_config, 'ControlPersist', 'ControlPersist\t10m')
    rewrite(ssh_config, 'ServerAliveInterval', 'ServerAliveInterval\t30')
    rewrite(ssh_config, 'ForwardAgent', 'ForwardAgent\t\tyes')

gitcfg = '''[user]
        name = %s
        email = %s
[core]
        editor = %s
[merge]
        tool = meld
[color]
        ui = auto
[alias]
        s = status
        st = status
        d = diff
        br = branch
        co = checkout
        ci = commit'''
def git_config(name='shell909090', email='shell909090@gmail.com', editor='vim'):
    ''' setup git config '''
    operations.put(StringIO(gitcfg % (name, email, editor)), '.gitconfig')

def emacs():
    ''' download and setup emacs '''
    pkgs = ['git', 'make', 'emacs', 'auto-complete-el', 'dictionary-el',
            'emacs-goodies-el', 'color-theme', 'magit', 'php-elisp', 'slime']
    if files.exists('.emacs.d'): return
    api.sudo('aptitude install %s' % ' '.join(pkgs))
    api.run('git clone git://github.com/shell909090/emacscfg.git .emacs.d')
    api.run('make -C .emacs.d install')

def user_config():
    ''' config user '''
    bashrc()
    ssh_config()
    git_config()
