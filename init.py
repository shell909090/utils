#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-04-28
@author: shell.xu
'''
import os, sys, cmd, glob, stat, subprocess
import readline
from os import path
from getopt import getopt

def rewrite(filepath, callback):
    filepath = path.expanduser(filepath)
    try:
        with open(filepath) as fi: lines = fi.readlines()
    except (OSError, IOError): lines = []
    lines = callback(lines)
    with open(filepath, 'w+') as fo: fo.write(''.join(lines))

def apt_check_and_install(names):
    names = [name for name in names if subprocess.call(
            ['dpkg-query', '-s', name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE) != 0]
    if names: subprocess.call(['aptitude', 'install'] + names)

def replace_if_or_append(s):
    def __inner(lines):
        flags, sl = set(), s.items()
        for i, l in enumerate(lines):
            for k, v in sl:
                if l.find(k) == -1: continue
                flags.add(k)
                lines[i] = v + '\n'
        for k in list(set(s.keys()) - flags):
            lines.append(s[k] + '\n')
        return lines
    return __inner

envcfg = {}

def getenv(name, prompt):
    dft = envcfg.get(name)
    return raw_input(prompt % dft) or dft

#
# system commands begin
#

def initenv(args):
    pass

debian_release = 'wheezy'
apt_src = [
    'http://mirrors.ustc.edu.cn/debian/',
    'http://mirrors.yun-idc.com/debian/',
    'http://localhost:9999/debian/',
    'http://srv/debian/']
def aptsrc():
    ''' auto setup apt source.
    	-r: debian release.'''
    global args
    optlist, args = getopt(args, 'r:')
    optdict = dict(optlist)
    for i, l in enumerate(apt_src): print i + 1, l
    chooses = [int(i.strip()) for i in raw_input('choose> ').split(',')]
    s = ['%sdeb %s %s main contrib non-free' % (
            '' if i+1 in chooses else '# ', l.strip(),
            optdict.get('-r') or debian_release)
         for i, l in enumerate(apt_src)]
    with open('/etc/apt/sources.list', 'w') as fo:
        fo.write('# from init.py\n' + '\n'.join(s))
    os.system('aptitude update')

def aptinst():
    ''' auto install packages. '''
    apt_check_and_install([
            'less', 'vim', 'mtr-tiny', 'sysv-rc-conf',
            'ifstat', 'iftop', 'sysv-rc-conf'])

def sshd_config():
    ''' setup sshd. '''
    rewrite('/etc/ssh/sshd_config',
            replace_if_or_append({
                'PasswordAuthentication': 'PasswordAuthentication no',
                'PermitRootLogin': 'PermitRootLogin no',
                'UseDNS': 'UseDNS no'}))

def fail2ban():
    ''' install fail2ban. '''
    apt_check_and_install(['fail2ban'])

def sshd_hostkey():
    ''' reset host key of ssh server. '''
    for p in glob.glob('/etc/ssh/*host*'): os.remove(p)
    os.system('dpkg-reconfigure openssh-server')

def ipXtables(name, cmd, tgtfile):
    global args
    optlist, args = getopt(args, 'p')
    optdict = dict(optlist)
    apt_check_and_install(['iptables-persistent'])
    accept_ports = raw_input('accept ports for %s (split by semicomma) [22]: ' % name) or '22'
    if '-p' not in optdict: do = os.system
    else: do = lambda x: sys.stdout.write(x+'\n')
    do('/etc/init.d/iptables-persistent flush')
    do('%s -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT' % cmd)
    do('%s -A INPUT -i lo -j ACCEPT' % cmd)
    do('%s -A INPUT -p icmp -m icmp --icmp-type 8 -j ACCEPT' % cmd)
    for p in accept_ports.split(';'):
        if '-' in p or ',' in p:
            do('%s -A INPUT -p tcp -m multiport --dports %s -j ACCEPT' % (cmd, p))
        else: do('%s -A INPUT -p tcp -m tcp --dport %s -j ACCEPT' % (cmd, p))
    do('%s -P INPUT DROP' % cmd)
    if '-p' not in optdict:
        do('%s-save > %s' % (cmd, tgtfile))
        do('/etc/init.d/netfilter-persistent restart')

def iptables():
    ''' auto setup iptables.
        -p: print mode.'''
    ipXtables('ipv4', 'iptables', '/etc/iptables/rules.v4')

def ip6tables():
    ''' auto setup iptables.
        -p: print mode.'''
    ipXtables('ipv6', 'ip6tables', '/etc/iptables/rules.v6')

def sysctl():
    ''' setup sysctl. '''
    with open('/etc/sysctl.d/net.conf', 'w+') as fo:
        fo.write('''net.ipv4.tcp_congestion_control = bbr

net.core.rmem_default = 2621440
net.core.rmem_max = 16777216
net.core.wmem_default = 655360
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096	2621440	16777216
net.ipv4.tcp_wmem = 4096	655360	16777216''')
    os.system('sysctl -p /etc/sysctl.d/net.conf')

def service():
    ''' setup system services. '''
    os.system('sysv-rc-conf')
    os.system('dpkg-reconfigure locales')
    os.system('dpkg-reconfigure tzdata')
    os.system('ln -sf bash /bin/sh')

cmds = set(['aptsrc', 'aptinst', 'sshd_config', 'fail2ban', 'sshd_hostkey',
            'iptables', 'ip6tables', 'sysctl', 'service'])

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
        return replace_if_or_append({
                'EDITOR': 'export EDITOR=%s' % getenv('editor', 'editor [%s]: '),
                'DEBEMAIL': 'export DEBEMAIL=%s' % getenv('email', 'debemail [%s]: '),
                'DEBFULLNAME': 'export DEBFULLNAME="%s"' % getenv('name', 'debname [%s]: ')
                })(lines)
    rewrite('~/.bashrc', edit)

pubkeys = [
    'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIANXSjD8YRhbmqr5tyjwQIRnqi4BMGY2CPbiGf/3EvWf shell@201602',]
def pubkey():
    ''' deploy my ssh keys '''
    try:
        os.makedirs(path.expanduser('~/.ssh/'))
        os.chmod(path.expanduser('~/.ssh/'),
                 stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except OSError: pass
    rewrite('~/.ssh/authorized_keys', replace_if_or_append(
            dict([(k, k) for k in pubkeys])))
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
    ans1 = raw_input('will you use ControlMaster[no]? ') or 'no'
    if ans1.lower().startswith('y'):
        for name in ['ControlMaster', 'ControlPath', 'ControlPersist']:
            ssh_cfg[name] = ssh_cfg[name].strip(' #')
    rewrite('~/.ssh/config', replace_if_or_append(ssh_cfg))

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
    apt_check_and_install([
            'git', 'make', 'emacs', 'auto-complete-el', 'dictionary-el',
            'emacs-goodies-el', 'color-theme', 'magit'])
    os.system('git clone git://github.com/shell909090/emacscfg.git ~/.emacs.d')
    os.system('make -C ~/.emacs.d install')

if os.getuid() != 0:
    user_cmds = set(['user', 'pubkey', 'ssh_config', 'git_config', 'emacs'])
    cmds, initenv = user_cmds, user_initenv

def main():
    '''init tool v1.1 written by Shell.Xu.
    -h: help
    '''
    global args
    optlist, args = getopt(sys.argv[1:], 'h')
    optdict = dict(optlist)

    if '-h' in optdict or not args:
        print main.__doc__
        for c in sorted(cmds):
            print '    %s:%s' % (c, globals().get(c).__doc__)
        return

    if args: initenv(args)
    while args:
        if args[0] in cmds: globals().get(args.pop(0))()
        else:
            print '%s can\'t be recognized.' % args.pop(0)
            return

if __name__ == '__main__': main()
