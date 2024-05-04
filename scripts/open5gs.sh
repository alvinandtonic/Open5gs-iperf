set -x

# load configs 
source /local/repository/scripts/setup-config

### Enable IPv4/IPv6 Forwarding
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
sysctl -w net.ipv4.ip_nonlocal_bind=1
#echo "net.ipv4.ip_nonlocal_bind = 1" >> /etc/sysctl.conf
#sysctl -p /etc/sysctl.conf

# disable kernel sctp for now
modprobe -rf sctp

### Add NAT Rule
# Probably need to change these values?
sudo iptables -t nat -A POSTROUTING -s 10.45.0.2/16 ! -o ogstun -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -s 10.45.0.1/16 ! -o ogstun -j MASQUERADE
sudo ip6tables -t nat -A POSTROUTING -s 2001:230:cafe::/48 ! -o ogstun -j MASQUERADE


if [ -f $SRCDIR/open5gs-setup-complete ]; then
    echo "setup already ran; not running again"
    exit 0
fi

sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:open5gs/latest

#instaling wireshark

sudo add-apt-repository -y ppa:wireshark-dev/stable
echo "wireshark-common wireshark-common/install-setuid boolean false" | sudo debconf-set-selections
sudo apt -y install wireshark

#installing MongoDB

sudo apt update
sudo apt install gnupg
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

#installing Open5gs
sudo add-apt-repository ppa:open5gs/latest
sudo apt update
sudo apt install -y open5gs

#installing NodeJS for webUI

sudo apt update
 sudo apt install -y ca-certificates curl gnupg
 sudo mkdir -p /etc/apt/keyrings
 curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

 # Create deb repository
 NODE_MAJOR=20
 echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list

 # Run Update and Install
 sudo apt update
 sudo apt install nodejs -y

curl -fsSL https://open5gs.org/open5gs/assets/webui/install | sudo -E bash -

sudo systemctl restart open5gs-mmed
sudo systemctl restart open5gs-sgwcd
sudo systemctl restart open5gs-smfd
sudo systemctl restart open5gs-amfd
sudo systemctl restart open5gs-sgwud
sudo systemctl restart open5gs-upfd
sudo systemctl restart open5gs-hssd
sudo systemctl restart open5gs-pcrfd
sudo systemctl restart open5gs-nrfd
sudo systemctl restart open5gs-ausfd
sudo systemctl restart open5gs-udmd
sudo systemctl restart open5gs-pcfd
sudo systemctl restart open5gs-nssfd
sudo systemctl restart open5gs-bsfd
sudo systemctl restart open5gs-udrd
sudo systemctl restart open5gs-webui

# clone open5gs for dbctl script
cd /root
git clone https://github.com/open5gs/open5gs
cd open5gs/misc/db


#add default ue subscriber so user doesn't have to log into web ui
opc="E8ED289DEBA952E4283B54E88E6183CA"
upper=$(($NUM_UE_ - 1))
for i in $(seq 0 $upper); do
    newkey=$(printf "%0.s$i" {1..32}) # example: 33333333333333333333333333333333
    ./open5gs-dbctl add 99970000000000$i $newkey $opc
done                                              

#./open5gs-dbctl add 901700000000001 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA

echo "Setup 4G/ 5G NSA Core"

cp /local/repository/config/mme.yaml /etc/open5gs/mme.yaml
cp /local/repository/config/sgwu.yaml /etc/open5gs/sgwu.yaml

echo "Setup 5G Core"

cp /local/repository/config/amf.yaml /etc/open5gs/amf.yaml
cp /local/repository/config/upf.yaml /etc/open5gs/upf.yaml

sudo systemctl restart open5gs-mmed
sudo systemctl restart open5gs-sgwud
sudo systemctl restart open5gs-amfd
sudo systemctl restart open5gs-upfd
