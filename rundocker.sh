#! /bin/bah

apt-get update
apt-get install -y python3 python3-venv nodejs npm jq chromium
apt-get clean
python3 -m venv venv
source venv/bin/activate
npm install
useradd user
su user -c /bin/bash << EOSU
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 crawl.py -c crawl.yaml
EOSU
#while true; do sleep 100; done
