echo "Codice_IPA,url,lighthouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia" > entiRes.csv
find entiRes -name \*.json -exec jq -r '[.Codice_IPA,.url,.lighthouseScore,."first-meaningful-paint".numericValue,."total-byte-weight".numericValue,.bootstrapItalia.bootstrap,.bootstrapItalia.bootstrapItalia] | @csv' '{}' \; | tee -a entiRes.csv
