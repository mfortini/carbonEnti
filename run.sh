#! /bin/bash


killall Xvfb

sleep 1

Xvfb :1 &

while true
do
	curl -o enti.csv 'https://indicepa.gov.it/ipa-dati/datastore/dump/d09adf99-dc10-4349-8c53-27b1e5aa97b6?bom=True'
	python3 crawl.py -c crawl.yaml > ../crawl.log 2>&1 
	git add enti.csv entiRes
        git commit -m "run $(date)"
        sleep 3600
done 
