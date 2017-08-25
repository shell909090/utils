#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2015-08-13
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from __future__ import absolute_import, division,\
    print_function, unicode_literals
import os
import re
import readline
import StringIO
if __name__ == '__main__':
    from fakefab import env, sudo, run, get, put, task, hide, settings
else:
    from fabric.api import env, sudo, run, get, put, task, hide, settings


try:
    input = raw_input
except NameError:
    pass


env.use_ssh_config = True
env.roledefs['debox'] = [
    'srv', 'web', 'pub', 'router', 'debox']
env.roledefs['vps'] = [
    'buyvm', 'do1', 'vlt1']


config = {
    'name': 'Xu ZhiXiang (Shell.E.Xu)',
    'email': 'shell909090@gmail.com',
    'editor': 'vim',
    'signingkey': '227657F36E169B9041862EBF29A973860914A01A',
    'ControlMaster': 'auto',
    'apt_source': 'https://mirrors.shell909090.org/debian/',
    'apt_dest': 'jessie'
}


class RemoteFile(object):

    def __init__(self, filepath, use_sudo=False):
        self.filepath, self.use_sudo = filepath, use_sudo
        buf = StringIO.StringIO()
        with settings(warn_only=True):
            get(self.filepath, buf, use_sudo=self.use_sudo)
        self.content = buf.getvalue()

    def update(self):
        buf = StringIO.StringIO()
        buf.seek(0, os.SEEK_SET)
        buf.truncate()
        buf.write(self.content)
        buf.seek(0, os.SEEK_SET)
        put(buf, self.filepath, self.use_sudo)


def rlinput(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def find_or_add(s, regex, repl, replace=False):
    ''' try find regex in s.
if do, replace original string if flag replace setted, otherwise ignore.
if not find, add repl to the end. '''
    regex = re.compile(regex, re.MULTILINE)
    m = regex.search(s)
    if m:
        if replace:
            s = regex.sub(repl, s)
    elif callable(repl):
        s += '%s\n' % repl(None)
    else:
        s += '%s\n' % repl
    return s


def repl_rlinput(line, prompt, default):
    cache = {}

    def repl(m):
        if 'value' not in cache:
            d = default
            if m:
                g = m.groups()
                if g and g[0]:
                    d = g[0]
            cache['value'] = rlinput(prompt, d).strip()
        return line % cache['value']
    return repl


def confirm_content(content, filepath='', default=''):
    print('-----%s-----' % filepath)
    print(content)
    print('----------')
    answer = rlinput('Is this ok? ', default)
    return answer.lower().startswith('y')


@task
def apt_source():
    sources_path = '/etc/apt/sources.list'
    main_repo = re.compile(r'deb\s+(\S+)\s+(\S+)\s+(.*)', re.M)
    rf = RemoteFile(sources_path, use_sudo=True)

    m = main_repo.search(rf.content)
    url, dest, components = m.groups()
    rf.content = find_or_add(
        rf.content,
        url,
        repl_rlinput('%s', 'url: ', url),
        replace=True)
    rf.content = find_or_add(
        rf.content,
        dest,
        repl_rlinput('%s', 'destribution: ', dest),
        replace=True)
    rf.content = find_or_add(
        rf.content,
        components,
        repl_rlinput('%s', 'components: ', components),
        replace=True)
    if confirm_content(rf.content, sources_path, default='y'):
        rf.update()


@task
def upgrade():
    sudo('aptitude -q=2 update')
    sudo('aptitude -y full-upgrade')
    sudo('aptitude clean')
    sudo('aptitude forget-new')


@task
def check_dpkg():
    purge_list = []
    with hide('stdout'):
        for i, line in enumerate(str(run('dpkg -l')).splitlines()):
            if i < 6:
                continue
            if line.startswith(b'ii'):
                continue
            line = line.strip()
            if line.startswith(b'rc'):
                purge_list.append(line.split()[1])
                continue
            print(line)
    if purge_list:
        sudo('aptitude -y purge ' + ' '.join(purge_list))


def apt_check_and_install(name):
    with settings(warn_only=True):
        if sudo('dpkg-query -s {}'.format(name)).succeeded:
            return
    sudo('aptitude install {}'.format(name))


def get_port_list(result, protocol):
    for line in result.splitlines():
        if protocol not in line:
            continue
        line = line.strip()
        r = line.split()
        if 'multiport' in line:
            yield r[-1]
        else:
            yield r[-1].split(':')[-1]


MULTIPORT_CMD = '{} -A INPUT -p {} -m multiport --dports {} -j ACCEPT'
TCP_CMD = '{} -A INPUT -p {} -m {} --dport {} -j ACCEPT'


def set_ports(name, protocol, iptables_cmd, default):
    accept_ports = rlinput('{} ports for {}: '.format(protocol, name), default)

    for p in accept_ports.split(';'):
        p = p.strip()
        if not p:
            continue
        if '-' in p or ',' in p:
            sudo(MULTIPORT_CMD.format(iptables_cmd, protocol, p))
        else:
            sudo(TCP_CMD.format(iptables_cmd, protocol, protocol, p))


@task
def iptables():
    with hide('stdout'):
        rules = sudo('iptables -n -v -L INPUT')
    tcpports = ';'.join(get_port_list(rules, 'tcp')) or '22'
    udpports = ';'.join(get_port_list(rules, 'udp'))
    sudo('iptables -P INPUT ACCEPT')
    sudo('iptables -F INPUT')
    sudo('iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT')
    sudo('iptables -A INPUT -i lo -j ACCEPT')
    sudo('iptables -A INPUT -p icmp -j ACCEPT')
    print('split by semicolon, just semicolon for none')
    if '22' not in tcpports:
        print('WARNING: ssh default port not in tcp list,\
 this may cause connection broken.')
    set_ports('ipv4', 'tcp', 'iptables', tcpports)
    set_ports('ipv4', 'udp', 'iptables', udpports)
    sudo('iptables -P INPUT DROP')


@task
def ip6tables():
    with hide('stdout'):
        rules = sudo('ip6tables -n -v -L INPUT')
    tcpports = ';'.join(get_port_list(rules, 'tcp')) or '22'
    udpports = ';'.join(get_port_list(rules, 'udp'))
    sudo('ip6tables -P INPUT ACCEPT')
    sudo('ip6tables -F INPUT')
    sudo('ip6tables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT')
    sudo('ip6tables -A INPUT -i lo -j ACCEPT')
    sudo('ip6tables -A INPUT -p ipv6-icmp -j ACCEPT')
    print('line split by semicolon.')
    if '22' not in tcpports:
        print('WARNING: ssh default port not in tcp list,\
 this may cause connection broken.')
    set_ports('ipv6', 'tcp', 'ip6tables', tcpports)
    set_ports('ipv6', 'udp', 'ip6tables', udpports)
    sudo('ip6tables -P INPUT DROP')


@task
def iptables_save():
    apt_check_and_install('iptables-persistent')
    sudo('iptables-save > {}'.format('/etc/iptables/rules.v4'))
    sudo('ip6tables-save > {}'.format('/etc/iptables/rules.v6'))
    sudo('service netfilter-persistent restart')


@task
def service():
    sudo('ln -sf bash /bin/sh')


@task
def chtz_sh():
    sudo('echo "Asia/Shanghai" > /etc/timezone')
    sudo('DEBIAN_FRONTEND=noninteractive dpkg-reconfigure tzdata')


@task
def sysctl():
    netconf = '/etc/sysctl.d/net.conf'
    buf = StringIO.StringIO(b'''\
net.ipv4.tcp_congestion_control = htcp

net.core.rmem_default = 2621440
net.core.rmem_max = 16777216
net.core.wmem_default = 655360
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096	2621440	16777216
net.ipv4.tcp_wmem = 4096	655360	16777216
net.ipv4.tcp_retries2 = 8
''')
    put(buf, netconf, use_sudo=True)
    sudo('chown root.root %s' % netconf)
    sudo('sysctl -p /etc/sysctl.d/net.conf')


@task
def fail2ban():
    apt_check_and_install('fail2ban')


@task
def sysutils():
    for s in ['less', 'vim', 'mtr-tiny', 'sysv-rc-conf',
              'ifstat', 'iftop', 'wget']:
        apt_check_and_install(s)


def ssh_secure(content):
    content = find_or_add(
        content,
        r'^[# ]*KexAlgorithms\s*(\S+)$',
        'KexAlgorithms curve25519-sha256@libssh.org,\
diffie-hellman-group-exchange-sha256',
        replace=True)
    content = find_or_add(
        content,
        r'^[# ]*Ciphers\s*(\S+)$',
        'Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,\
aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr',
        replace=True)
    content = find_or_add(
        content,
        r'^[# ]*MACs\s*(\S+)$',
        'MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,\
hmac-ripemd160-etm@openssh.com,umac-128-etm@openssh.com,hmac-sha2-512,\
hmac-sha2-256,hmac-ripemd160,umac-128@openssh.com',
        replace=True)
    return content


@task
def sshd_config():
    rf = RemoteFile('/etc/ssh/sshd_config', use_sudo=True)
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*PasswordAuthentication\s*(\S+)$',
        'PasswordAuthentication no',
        replace=True)
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*PermitRootLogin\s*(\S+)$',
        'PermitRootLogin no',
        replace=True)
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*UseDNS\s*(\S+)$',
        'UseDNS no',
        replace=True)
    rf.content = ssh_secure(rf.content)
    rf.update()


@task
def emacscfg():
    for s in ['git', 'make', 'emacs', 'auto-complete-el', 'dictionary-el',
              'emacs-goodies-el', 'color-theme', 'magit']:
        apt_check_and_install(s)


@task
def user_env():
    homedir = str(run("dirname ~/.bashrc")).strip()
    prefixes = ['/usr/local', '/usr', '', ]
    pathes = ':'.join(['%s/sbin:%s/bin' % (p, p) for p in prefixes])
    env_path = 'PATH="%s:%s/bin"' % (pathes, homedir)

    rf = RemoteFile('~/.bashrc')
    rf.content = find_or_add(
        rf.content,
        r'^PATH=(.*)$',
        env_path)
    rf.content = find_or_add(
        rf.content,
        r'^export EDITOR="?([^"]*)"?$',
        repl_rlinput('export EDITOR="%s"', 'editor: ', config['editor']))
    rf.update()


@task
def deb_env():
    rf = RemoteFile('~/.bashrc')
    rf.content = find_or_add(
        rf.content,
        '^export DEBEMAIL=(.*)$',
        repl_rlinput('export DEBEMAIL="%s"', 'deb email: ', config['email']))
    rf.content = find_or_add(
        rf.content,
        '^export DEBFULLNAME=(.*)$',
        repl_rlinput('export DEBFULLNAME="%s"',
                     'deb fullname: ', config['name']))
    rf.update()


GITCFG = '''[user]
        name = %s
        email = %s
        signingkey = %s
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
        ci = commit
[push]
        default = simple
'''


@task
def git_config():
    buf = StringIO.StringIO(GITCFG % (
        rlinput('name: ', config['name']),
        rlinput('email: ', config['email']),
        rlinput('signingkey: ', config['signingkey']),
        rlinput('editor: ', config['editor']),
    ))
    put(buf, '~/.gitconfig')


@task
def pubkey():
    pubkeys = [
        'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIANXSjD8YRh\
bmqr5tyjwQIRnqi4BMGY2CPbiGf/3EvWf shell@201602',
        'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJMb4giDpPu\
Vu0qi6YT9KhoK/dIidy6TE4OlocuchWFR mobile@201602'
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


@task
def ssh_config():
    rf = RemoteFile('~/.ssh/config')
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*ControlMaster\s*(\S+)$',
        repl_rlinput('ControlMaster\t%s',
                     'ControlMaster: ', config['ControlMaster']),
        replace=True)
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*ControlPath\s*(\S+)$',
        'ControlPath\t/tmp/ssh_mux_%h_%p_%r')
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*ControlPersist\s*(\S+)$',
        'ControlPersist\t10m')
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*ServerAliveInterval\s*(\S+)$',
        'ServerAliveInterval\t30')
    rf.content = find_or_add(
        rf.content,
        r'^[# ]*ForwardAgent\s*(\S+)$',
        'ForwardAgent\tno')
    # those config must on the top of the file.
    # otherwise they may be just work for lastest 'Host',
    # not all of them.
    # rf.content = ssh_secure(rf.content)
    rf.update()


def print_help():
    import fakefab
    print(main.__doc__)
    print('\t' + '\n\t'.join(sorted(fakefab.tasks.keys())))
    return


def main():
    '''python fabfile.py command.
available commands: '''
    import sys
    import getopt

    optlist, args = getopt.getopt(sys.argv[1:], 'h')
    optdict = dict(optlist)
    if '-h' in optdict:
        return print_help()

    if not args:
        print_help()
        return

    f = globals().get(args[0], print_help)
    f()


if __name__ == '__main__':
    main()
