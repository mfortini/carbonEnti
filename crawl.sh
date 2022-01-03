#! /bin/bash
csvgrep -c "Codice_natura" -m "2430" enti.csv   | csvcut -c "Denominazione_ente,Sito_istituzionale" | csvtool drop 1 - | csvtool  call 'bash calcCarbon.sh'  - > results.json
