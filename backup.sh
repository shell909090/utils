#!/bin/bash

TGT="$1"
if [[ "$TGT" == *.tar.gz.gpg ]]; then
    TGT=${TGT::-11}
fi
rm -f "$TGT.tar.gz.gpg"

read -s -p "Enter your password: " PASSWORD
echo ''

echo "create backup."
ssh "$TGT" <<EOF
pushd .
TMPDIR=\$(mktemp -d)
cd \$TMPDIR
apt-mark showmanual > apt-mark-manual.lst
dpkg -l > dpkg.lst
tar uf backup.tar apt-mark-manual.lst dpkg.lst ~/service ~/configs > /dev/null
FULLPATH=\$(realpath ~/configs)
echo $PASSWORD | sudo -S bash -c "while read i; do tar uf backup.tar \\\$i; done < \$FULLPATH"
test -x ~/backup.sh && tar uf backup.tar ~/backup.sh
test -x ~/backup.sh && ~/backup.sh
echo $PASSWORD | sudo -S chown \$SUDO_UID:\$SUDO_GID backup.tar
gzip -c backup.tar > ~/backup.tar.gz
popd
rm -rf \$TMPDIR
EOF

echo "copy backup back"
ssh "$TGT" 'cat backup.tar.gz' | gpg -e -r 0xC9A514BA45DE0475! > "$TGT.tar.gz.gpg"

echo "cleanup remote"
ssh "$TGT" 'rm -rf ~/backup.tar.gz'
