#!/bin/bash

NAME="Shell.Xu"
EMAIL="shell909090@gmail.com"
EDITOR="vim"

_update() {
  wget -O init.new 'https://github.com/shell909090/utils/raw/master/init.sh' && mv init.new init.sh && chmod +x init.sh
}

_aptsrc() {
    CFG=/etc/apt/sources.list
    if [ ! -e $CFG ]; then
	cat > $CFG <<EOF
deb http://ftp.cn.debian.org/debian/ bookworm main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb http://ftp.cn.debian.org/debian/ bookworm-updates main contrib non-free non-free-firmware
deb http://ftp.cn.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
EOF
    fi
}

_aptproxy() {
    CFG=/etc/apt/apt.conf.d/98proxy
    if [ ! -e $CFG ]; then
	cat > $CFG <<EOF
Acquire::http::Proxy "http://router.lan:8118/";
EOF
    fi
}

_aptipv4() {
    CFG=/etc/apt/apt.conf.d/99force-ipv4
    if [ ! -e $CFG ]; then
	cat > $CFG <<EOF
Acquire::ForceIPv4 "true";
EOF
    fi
}

_aptinst() {
    apt-get install aptitude -y
    aptitude install sudo less curl wget -y
    aptitude install isc-dhcp-client iputils-ping mtr-tiny netcat-openbsd -y
    # dnsutils - too big
    aptitude install vim nano htop tmux -y
}

set-ssh-config() {
    key="$1"
    value="$2"
    sed -i "s/^\W*$key [^\.,]*/$key $value/" "$CFG"
    if ! grep "$key $value" "$CFG" > /dev/null
    then
	echo "$key $value" >> "$CFG"
    fi
}

_sshd-config() {
    CFG=/etc/ssh/sshd_config
    set-ssh-config "PasswordAuthentication" "no"
    set-ssh-config "PermitEmptyPasswords" "no"
    set-ssh-config "PermitRootLogin" "no"
    set-ssh-config "UseDNS" "no"
}

_sshd-hostkey() {
    rm /etc/ssh/*host*
    dpkg-reconfigure openssh-server
}

ipXtables() {
    read -p "open ports [$1]: " ports
    if [ -z "$ports" ]; then
	ports="22"
    fi

    $IPT -F
    $IPT -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
    $IPT -A INPUT -i lo -j ACCEPT
    if [ "$1" == "ipv4" ]; then
	$IPT -A INPUT -p icmp -j ACCEPT
    else
	$IPT -A INPUT -p ipv6-icmp -j ACCEPT
    fi
    $IPT -A INPUT -p tcp -m multiport --dports "$ports" -j ACCEPT
    $IPT -P INPUT DROP
    $IPT-save
}

_iptables() {
    IPT=iptables
    if [ ! -e /etc/iptables/rules.v4 ]; then
	aptitude install -y iptables-persistent
	ipXtables ipv4 > /etc/iptables/rules.v4
    fi
}

_ip6tables() {
    IPT=ip6tables
    if [ ! -e /etc/iptables/rules.v6 ]; then
	aptitude install -y iptables-persistent
	ipXtables ipv6 > /etc/iptables/rules.v6
    fi
}

_sysctl() {
    CFG=/etc/sysctl.d/net.conf
    if [ ! -e $CFG ]; then
	cat > $CFG <<EOF
net.ipv4.tcp_congestion_control = bbr
net.core.rmem_default = 2621440
net.core.rmem_max = 16777216
net.core.wmem_default = 655360
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 2621440 16777216
net.ipv4.tcp_wmem = 4096 655360 16777216
net.ipv4.tcp_retries2 = 8
EOF
	sysctl -p /etc/sysctl.d/net.conf
    fi
}

_service() {
    dpkg-reconfigure locales
    dpkg-reconfigure tzdata
    ln -sf bash /bin/sh
}

set-bash-config() {
    key="$1"
    value="$2"
    sed -i "s/^\W*$key=.*/$key=\"$value\"/" "$CFG"
    if ! grep "$key=\"$value\"" "$CFG" > /dev/null
    then
	echo "$key=\"$value\"" >> "$CFG"
    fi
}

_user() {
    CFG=~/.bashrc
    if ! grep '^PATH' "$CFG"
    then
	sed -i '1iPATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"' "$CFG"
    fi
    set-bash-config "export EDITOR" "$EDITOR"
    set-bash-config "export DEBEMAIL" "$EMAIL"
    set-bash-config "export DEBFULLNAME" "$NAME"
}

_pubkey() {
    mkdir -p ~/.ssh/
    chmod 700 ~/.ssh/
    if [[ ! -e ~/.ssh/authorized_keys ]]; then
	touch ~/.ssh/authorized_keys
    fi
    if ! grep 'shell@201602' ~/.ssh/authorized_keys
    then
	cat >> ~/.ssh/authorized_keys <<EOF
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIANXSjD8YRhbmqr5tyjwQIRnqi4BMGY2CPbiGf/3EvWf shell@201602
EOF
    fi
    if ! grep '202302' ~/.ssh/authorized_keys
    then
	cat >> ~/.ssh/authorized_keys <<EOF
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMPG3Ci4r5R/coysaSe4Dbsbd+R5lYtXXFVG2Hx2NAIg 202302
EOF
    fi
    chmod 600 ~/.ssh/authorized_keys
}

_ssh-config() {
    CFG=~/.ssh/config
    if [ ! -e $CFG ]; then
	cat > $CFG <<EOF
ServerAliveInterval	30
ForwardAgent		no
# ControlMaster		auto
# ControlPath		/tmp/ssh_mux_%h_%p_%r
# ControlPersist	10m
EOF
    fi
}

_git-config() {
    CFG=~/.gitconfig
    if [ ! -e $CFG ]; then
	cat > $CFG <<EOF
[user]
        name = $NAME
        email = $EMAIL
[core]
        editor = $EDITOR
[merge]
        tool = meld
[color]
        ui = auto
[alias]
        s = status
        st = status
        sw = switch
        f = fetch
        d = diff
        br = branch
	rb = rebase
        co = checkout
        ci = commit
	lg = log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit
[init]
	templatedir = ~/.git_template
	defaultBranch = main
[pull]
	ff = only
[push]
	default = current
EOF
    fi
}

_emacs() {
    if [ ! -e ~/.emacs.d ]; then
	aptitude install git make emacs auto-complete-el dictionary-el emacs-goodies-el color-theme magit
	git clone git://github.com/shell909090/emacscfg.git ~/.emacs.d
	make -C ~/.emacs.d install
    fi
}

_help() {
    declare -F | while read line;
    do
	if [ ${line:11:1} == "_" ]; then
	    echo ${line:12}
	fi
    done
}

fn="$1"
shift
if declare -F "_$fn" > /dev/null
then
    "_$fn" "$@"
else
    _help
fi
