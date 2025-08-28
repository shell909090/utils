#!/bin/bash

aptitude update
apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common

curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
cat <<EOF >/etc/apt/sources.list.d/docker.list
deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable
EOF
apt-get update
apt-get install -y docker-ce

curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt-get update
apt-get install -y kubelet kubeadm kubectl
