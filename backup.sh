#!/bin/bash

rm -f "$1.tar.gz.gpg"
TMPDIR=`ssh "$1" "mktemp -d"`
echo "create tempdir $TMPDIR"
ssh "$1" <<EOF
cd $TMPDIR
apt-mark showmanual > apt-mark-manual.lst
dpkg -l > dpkg.lst
tar uf backup.tar apt-mark-manual.lst dpkg.lst ~/service ~/configs
sudo bash -c 'while read i; do tar uf backup.tar \$i; done' < ~/configs
test -x ~/backup.sh && tar uf backup.tar ~/backup.sh
test -x ~/backup.sh && ~/backup.sh
sudo chown $SUDO_UID.$SUDO_GID backup.tar
EOF
ssh "$1" "gzip -c $TMPDIR/backup.tar" | gpg -e > "$1.tar.gz.gpg"
ssh "$1" "rm -rf \"$TMPDIR\""
