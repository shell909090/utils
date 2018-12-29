#!/bin/bash

TGT="$1"
if [[ "$TGT" == *.tar.gz.gpg ]]; then
    TGT=${TGT::-11}
fi
rm -f "$TGT.tar.gz.gpg"
TMPDIR=`ssh "$TGT" "mktemp -d"`
echo "create tempdir $TMPDIR"
ssh "$TGT" <<EOF
cd $TMPDIR
apt-mark showmanual > apt-mark-manual.lst
dpkg -l > dpkg.lst
tar uf backup.tar apt-mark-manual.lst dpkg.lst ~/service ~/configs
sudo bash -c 'while read i; do tar uf backup.tar \$i; done' < ~/configs
test -x ~/backup.sh && tar uf backup.tar ~/backup.sh
test -x ~/backup.sh && ~/backup.sh
sudo chown $SUDO_UID.$SUDO_GID backup.tar
EOF
ssh "$TGT" "gzip -c $TMPDIR/backup.tar" | gpg -e > "$TGT.tar.gz.gpg"
ssh "$TGT" "rm -rf \"$TMPDIR\""
