#!/bin/bash

rm -f "$1.tar.gz.gpg"
ssh "$1" "rm -f backup.tar.gz"
ssh "$1" "sudo bash -c 'while read i; do tar uf backup.tar \$i; done' < configs"
ssh "$1" "sudo chown $SUDO_UID.$SUDO_GID backup.tar"
ssh "$1" "gzip -c backup.tar" | gpg2 -e > "$1".tar.gz.gpg
# ssh "$1" "gzip -c backup.tar" > "$1".tar.gz
ssh "$1" "rm -f backup.tar"
