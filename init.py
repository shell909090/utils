#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-04-28
@author: shell.xu
'''
import os, sys, cmd, glob, stat, getopt
import readline
from os import path

def rewrite(filepath, callback):
    filepath = path.expanduser(filepath)
    try:
        with open(filepath) as fi: lines = fi.readlines()
    except (OSError, IOError): lines = []
    lines = callback(lines)
    with open(filepath, 'w+') as fo: fo.write(''.join(lines))

def setup(lines, s):
    flags = {}
    for i, l in enumerate(lines):
        for k, v in s:
            if l.find(k) != -1:
                flags[k] = True
                lines[i] = v + '\n'
    for k, v in s:
        if not flags.get(k): lines.append(v + '\n')
    return lines

def apt_source():
    ''' auto setup apt source '''
    for p in ['/etc/apt/sources.list', '/etc/apt/sources.list.d/debian.list']:
        if path.exists(p): f = p
    with open(f, 'w') as fo:
        fo.write('''# from init.py
deb http://mirrors.ustc.edu.cn/debian/ wheezy main contrib non-free
#deb http://mirrors.yun-idc.cn/debian/ wheezy main contrib non-free
#deb http://localhost:9999/debian/ wheezy main contrib non-free''')

def apt_install():
    ''' auto install packages '''
    pkglist = ['less', 'vim', 'mtr-tiny', 'sysv-rc-conf', 'ifstat', 'iftop',
               'iptables-persistent', 'sysv-rc-conf']
    os.system('aptitude install %s' % ' '.join(pkglist))

def sshd():
    ''' setup sshd '''
    os.system('aptitude install denyhosts')
    def edit(lines):
        return setup(lines, [
                ('PasswordAuthentication', 'PasswordAuthentication no'),
                ('PermitRootLogin', 'PermitRootLogin no'),
                ('UseDNS', 'UseDNS no')])
    rewrite('/etc/ssh/sshd_config', edit)

def sshd_hostkey():
    ''' reset host key of ssh server '''
    for p in glob.glob('/etc/ssh/*host*'): os.remove(p)
    os.system('dpkg-reconfigure openssh-server')

pubkeys = [
    ('shell@debox', 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDWECakpfuC1j/VbaAotYcfIuNFsw3MNH1epFfZRHfNMRfSblDdom22zOlLSe40qTJvcXGCGqGKKuL2TcYdlrCpAvIM9+xNxuPIJQbeZ4egmC0uCf/YiEuy6QeFb/c7/CQJ3qnhjUc7w65MvX7fwBFgKy6G0IZOOh5QD4cYZf2u1cAqAHxIWztdZfbTEpo9DHkYZlyd5QbhfnOqe4OGgTsXi2wMLeSWQGmRx59Tu1Rtds2HZZRt7dzgx6itR60M/GTa5IqTOeBPbYGgtoc4OAAeqtUqzYoN9EO/yjTzEzb4tKPku1juWvOc5sJtcLDGt4nM7jrCIsssm+1ODKGAhJf shell@debox')]
def ssh_pubkey():
    ''' deploy my ssh keys '''
    def edit(lines): return setup(lines, pubkeys)
    rewrite('~/.ssh/authorized_keys', edit)
    os.chmod(path.expanduser('~/.ssh/authorized_keys'),
             stat.S_IRUSR | stat.S_IWUSR)

def sudo():
    ''' sudo username to setup user can sudo to root '''
    username = args.pop(1)
    with open('/etc/sudoers.d/%s' % username, 'w+') as fo:
        fo.write('%s   ALL=(ALL) NOPASSWD: ALL' % username)
    os.chmod('/etc/sudoers.d/%s' % username, stat.S_IRUSR)

def ipXtables(name, cmd, tgtfile):
    accept_ports = raw_input('accept ports for %s (split by semicomma) [22]: ' % name)
    if not accept_ports: accept_ports = '22'
    if '-p' not in optdict: do = os.system
    else: do = lambda x: sys.stdout.write(x+'\n')
    do('/etc/init.d/iptables-persistent flush')
    do('%s -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT' % cmd)
    do('%s -A INPUT -i lo -j ACCEPT' % cmd)
    for p in accept_ports.split(';'):
        if '-' in p or ',' in p:
            do('%s -A INPUT -p tcp -m multiport --dports %s -j ACCEPT' % (cmd, p))
        else: do('%s -A INPUT -p tcp -m tcp --dport %s -j ACCEPT' % (cmd, p))
    do('%s -P INPUT DROP' % cmd)
    if '-p' not in optdict:
        do('%s-save > %s' % (cmd, tgtfile))
    do('/etc/init.d/iptables-persistent restart')

def iptables():
    ''' auto setup iptables, use -p to print out. '''
    ipXtables('ipv4', 'iptables', '/etc/iptables/rules.v4')

def ip6tables():
    ''' auto setup iptables for ipv6, use -p to print out. '''
    ipXtables('ipv6', 'ip6tables', '/etc/iptables/rules.v6')

def sysctl():
    ''' setup sysctl. '''
    with open('/etc/sysctl.d/net.conf', 'w+') as fo:
        fo.write('net.ipv4.tcp_congestion_control = htcp')
    os.system('sysctl -p /etc/sysctl.d/net.conf')

def service():
    ''' setup system services. '''
    os.system('sysv-rc-conf')
    os.system('dpkg-reconfigure locales')
    os.system('dpkg-reconfigure tzdata')

def shelllink():
    ''' link /bin/sh to bash. '''
    os.system('ln -sf bash /bin/sh')

envpath = ['/usr/local/sbin', '/usr/local/bin', '/usr/sbin',
           '/usr/bin', '/sbin', '/bin', '~/bin']
def user():
    ''' setup user environment. '''
    def edit(lines):
        editor = raw_input('editor [vim]: ')
        if not any([l.find('PATH') != -1 for l in lines]):
            for i, l in enumerate(lines):
                if not l.startswith('#'): break
            lines.insert(i, 'PATH="%s"\n' % ':'.join(envpath))
        return setup(lines, [
                ('EDITOR', 'export EDITOR=%s' % editor),
                ('DEBEMAIL', 'export DEBEMAIL=shell909090@gmail.com'),
                ('DEBFULLNAME', 'export DEBFULLNAME="Shell Xu"')])
    rewrite('~/.bashrc', edit)

cmds = set(['apt_source', 'apt_install', 'sshd', 'sshd_hostkey',
            'ssh_pubkey', 'sudo', 'iptables', 'ip6tables',
            'sysctl', 'service', 'shelllink', 'user'])
default_args = [
    'apt_source', 'apt_install', 'sshd', 'sshd_hostkey', 'ssh_pubkey', 'sudo',
    'shell', 'iptables', 'ip6tables', 'sysctl', 'service', 'shelllink', 'user']
def main():
    '''init tool v1.0 written by Shell.Xu.
    -a: do all commands
    -h: help
    -p: print mode in iptables and ip6tables.
    -u: username
commands:'''
    global optdict
    global args
    optlist, args = getopt.getopt(sys.argv[1:], 'ahpu:')
    optdict = dict(optlist)

    if '-a' in optdict: args = default_args
    if '-h' in optdict or not args:
        print main.__doc__
        for c in sorted(cmds):
            print '    %s:%s' % (c, globals().get(c).__doc__)
        return

    while args:
        if args[0] in cmds: globals().get(args.pop(0))()
        else: print '%s can\'t be recognized.' % args.pop(0)

if __name__ == '__main__': main()
