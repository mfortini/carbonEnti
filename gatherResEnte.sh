#! /bin/bash

filename=$1

Codice_IPA=$(basename "${filename}" .json)

line=$(jq -r '[.url,.lighthouseScore,."first-meaningful-paint".numericValue,."total-byte-weight".numericValue,.bootstrapItalia.bootstrap,.bootstrapItalia.bootstrapItalia,.bootstrapItalia.bootstrapItaliaVariable,.bootstrapItalia.bootstrapItaliaMethod] | @csv' "${filename}")

echo ${Codice_IPA},${line}
