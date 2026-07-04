#! /bin/bash

echo "Codice_IPA,url,lighthouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia,bootstrap2_js,bootstrap2_css" > entiRes.csv
find entiRes -name \*.json -exec ./gatherResEnte.sh '{}' \; | tee -a entiRes.csv
