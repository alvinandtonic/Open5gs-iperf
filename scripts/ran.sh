#!/bin/bash

# This script installs UERANSIM and its prerequisites on the ran node as root user then runs it. Configs still need to be adjusted.

# Any subsequent(*) commands which fail will cause the shell script to exit immediately
set -e

# load config values
source /local/repository/scripts/setup-config

# automate grub prompt during installation
echo "SET grub-pc/install_devices /dev/sda" | sudo debconf-communicate


echo "1. Install the UERANSIM dependencies."
cd ~
sudo apt -y --force-yes update 
DEBIAN_FRONTEND=noninteractive sudo apt -y --force-yes -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
sudo apt -y --force-yes install make g++ openjdk-11-jdk maven libsctp-dev lksctp-tools snapd
sudo apt install make gcc g++ libsctp-dev lksctp-tools iproute2 git

sudo snap install cmake --classic

git clone https://github.com/aligungr/UERANSIM

cp /local/repository/config/ueran-gnb.yaml ~/UERANSIM/config/open5gs-gnb.yaml
cp /local/repository/config/ueran-ue.yaml ~/UERANSIM/config/open5gs-ue.yaml

cd ~/UERANSIM
make
