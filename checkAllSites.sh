#! /bin/bash

echo Codice_IPA,HTTPCode,CurlExitStatus
csvcut -c "Codice_IPA,Sito_istituzionale" enti.csv | csvtool drop 1 - | csvtool call  'bash checkSite.sh' -
