#!/bin/bash

rm -f "$1.tar.gz.gpg"
ssh "$1" <<EOF
rm -f backup.tar
apt-mark showmanual > apt-mark-manual.lst
dpkg -l > dpkg.lst
tar uf backup.tar apt-mark-manual.lst dpkg.lst service configs
rm -f dpkg.lst apt-mark-manual.lst
sudo bash -c 'while read i; do tar uf backup.tar \$i; done' < configs
sudo chown $SUDO_UID.$SUDO_GID backup.tar
EOF
ssh "$1" "gzip -c backup.tar" | gpg -e > "$1".tar.gz.gpg
ssh "$1" "rm -f backup.tar"
