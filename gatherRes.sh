find entiRes -name \*.json -exec jq -r '[.Codice_IPA,.url,.lighthouseScore,."first-meaningful-paint".numericValue,."total-byte-weight".numericValue] | @csv' '{}' \; | tee entiRes.csv
