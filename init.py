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

envcfg = {}

def getenv(name, prompt):
    dft = envcfg.get(name)
    return raw_input(prompt % dft) or dft

#
# system commands begin
#

def initenv(args):
    pass

debian_release = 'jessie'
apt_src = [
    'http://mirrors.ustc.edu.cn/debian/',
    'http://mirrors.yun-idc.cn/debian/',
    'http://localhost:9999/debian/',
    'http://srv/debian/']
def apt_source():
    ''' auto setup apt source '''
    for p in ['/etc/apt/sources.list', '/etc/apt/sources.list.d/debian.list']:
        if path.exists(p): f = p
    for i, l in enumerate(apt_src): print i + 1, l
    chooses = [int(i.strip()) for i in raw_input('choose> ').split(',')]
    s = ['%sdeb %s %s main contrib non-free' % (
            '' if i+1 in chooses else '# ', l.strip(), debian_release)
         for i, l in enumerate(apt_src)]
    with open(f, 'w') as fo: fo.write('# from init.py\n' + '\n'.join(s))
    os.system('aptitude update')

def apt_install():
    ''' auto install packages '''
    os.system('aptitude install %s' % ' '.join([
                'less', 'vim', 'mtr-tiny', 'sysv-rc-conf',
                'ifstat', 'iftop', 'sysv-rc-conf']))

def sshd_config():
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

def sudo():
    ''' sudo username to setup user can sudo to root '''
    username = args.pop(1)
    with open('/etc/sudoers.d/%s' % username, 'w+') as fo:
        fo.write('%s   ALL=(ALL) NOPASSWD: ALL' % username)
    os.chmod('/etc/sudoers.d/%s' % username, stat.S_IRUSR)

def ipXtables(name, cmd, tgtfile):
    os.system('aptitude install iptables-persistent')
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

cmds = set(['apt_source', 'apt_install', 'sshd_config', 'sshd_hostkey',
            'sudo', 'iptables', 'ip6tables', 'sysctl', 'service', 'shelllink'])
default_args = [
    'apt_source', 'apt_install', 'sshd_config', 'sshd_hostkey', 'sudo',
    'shell', 'iptables', 'ip6tables', 'sysctl', 'service', 'shelllink']

#
# user commands begin
#

def user_initenv(args):
    if not (set(args) & set(['user', 'git_config'])): return
    envcfg['name'] = raw_input('name: ')
    envcfg['email'] = raw_input('email: ')
    envcfg['editor'] = raw_input('editor [vim]: ')  or 'vim'

envpath = ['/usr/local/sbin', '/usr/local/bin', '/usr/sbin',
           '/usr/bin', '/sbin', '/bin', '~/bin']
def user():
    ''' setup user environment. '''
    def edit(lines):
        if not any([l.find('PATH') != -1 for l in lines]):
            for i, l in enumerate(lines):
                if not l.startswith('#'): break
            lines.insert(i, 'PATH="%s"\n' % ':'.join(envpath))
        return setup(lines, [
                ('EDITOR', 'export EDITOR=%s' % getenv('editor', 'editor [%s]: ')),
                ('DEBEMAIL', 'export DEBEMAIL=%s' % getenv('email', 'debemail [%s]: ')),
                ('DEBFULLNAME', 'export DEBFULLNAME="%s"' % getenv('name', 'debname [%s]: '))])
    rewrite('~/.bashrc', edit)

pubkeys = [
    ('shell@debox', 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDWECakpfuC1j/VbaAotYcfIuNFsw3MNH1epFfZRHfNMRfSblDdom22zOlLSe40qTJvcXGCGqGKKuL2TcYdlrCpAvIM9+xNxuPIJQbeZ4egmC0uCf/YiEuy6QeFb/c7/CQJ3qnhjUc7w65MvX7fwBFgKy6G0IZOOh5QD4cYZf2u1cAqAHxIWztdZfbTEpo9DHkYZlyd5QbhfnOqe4OGgTsXi2wMLeSWQGmRx59Tu1Rtds2HZZRt7dzgx6itR60M/GTa5IqTOeBPbYGgtoc4OAAeqtUqzYoN9EO/yjTzEzb4tKPku1juWvOc5sJtcLDGt4nM7jrCIsssm+1ODKGAhJf shell@debox')]
def ssh_pubkey():
    ''' deploy my ssh keys '''
    def edit(lines): return setup(lines, pubkeys)
    rewrite('~/.ssh/authorized_keys', edit)
    os.chmod(path.expanduser('~/.ssh/authorized_keys'),
             stat.S_IRUSR | stat.S_IWUSR)

ssh_cfg = {
    'ControlMaster': '# ControlMaster\t\tauto',
    'ControlPath': '# ControlPath\t\t/tmp/ssh_mux_%h_%p_%r',
    'ControlPersist': '# ControlPersist\t10m',
    'ServerAliveInterval': 'ServerAliveInterval\t30',
    'ForwardAgent': 'ForwardAgent\t\tyes'}
def ssh_config():
    ''' setup ssh client config '''
    ans1 = raw_input('will you use ControlMaster[no]? ')
    if not ans1: ans1 = 'no'
    if ans1.lower().startswith('y'):
        for name in ['ControlMaster', 'ControlPath', 'ControlPersist']:
            ssh_cfg[name] = ssh_cfg[name].strip(' #')
    def edit(lines): return setup(lines, ssh_cfg.items())
    rewrite('~/.ssh/config', edit)

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
def git_config():
    ''' setup git config '''
    with open(path.expanduser('~/.gitconfig'), 'w') as fo:
        fo.write(gitcfg % (
                getenv('name', 'git name [%s]: '),
                getenv('email', 'git email [%s]: '),
                getenv('editor', 'git editor [%s]: ')))

def emacs():
    ''' download and setup emacs '''
    if path.exists(path.expanduser('~/.emacs.d')): return
    os.system('aptitude install %s' % ' '.join([
                'git', 'make', 'emacs', 'auto-complete-el',
                'dictionary-el', 'emacs-goodies-el', 'color-theme',
                'magit', 'php-elisp', 'slime']))
    os.system('git clone git://github.com/shell909090/emacscfg.git ~/.emacs.d')
    os.system('make -C ~/.emacs.d install')

user_cmds = set(['user', 'ssh_pubkey', 'ssh_config', 'git_config', 'emacs'])
user_default_args = ['user', 'ssh_pubkey', 'ssh_config', 'git_config', 'emacs']
if os.getuid() != 0:
    cmds, default_args, initenv = user_cmds, user_default_args, user_initenv

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

    if args: initenv(args)
    while args:
        if args[0] in cmds: globals().get(args.pop(0))()
        else: print '%s can\'t be recognized.' % args.pop(0)

if __name__ == '__main__': main()
