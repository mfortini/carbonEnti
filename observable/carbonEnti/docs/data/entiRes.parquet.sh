#! /bin/bash

filename=/tmp/entiRes.parquet
filename2=/tmp/entiResIPA.parquet


url_2022_02_11=https://raw.githubusercontent.com/mfortini/carbonEnti/172024cc177ff57455460a9235b9fb4f96d32f2d/entiRes.csv
url_2023_11_02=https://raw.githubusercontent.com/mfortini/carbonEnti/ce5141b5f3b2db53bb50c7e08fd48a90468f9642/entiRes.csv
url_2024_03_12=https://raw.githubusercontent.com/mfortini/carbonEnti/98aec540827cbe1cc1684c8552d89d591e81c38a/entiRes.csv
url_2024_07_31=https://raw.githubusercontent.com/mfortini/carbonEnti/2923492daadf776b3de0fd78bc75f0cea6900433/entiRes.csv

url_IPA=https://raw.githubusercontent.com/mfortini/carbonEnti/main/enti.csv
url_categorieIPA=https://raw.githubusercontent.com/mfortini/carbonEnti/main/entiCategorie.csv
url_entiCheck=https://raw.githubusercontent.com/mfortini/carbonEnti/main/entiCheck.csv
url_CurlExitStatuses=https://raw.githubusercontent.com/mfortini/carbonEnti/main/CurlExitStatuses.csv

duckdb -c "SET preserve_insertion_order=false;\
COPY (SELECT CAST ('2022-02-11' AS DATE) AS crawlDate,*, NULL AS bootstrap2_js, NULL AS bootstrap2_css FROM read_csv_auto('${url_2022_02_11}') \
UNION SELECT CAST ('2023-11-02' AS DATE) AS crawlDate,*, NULL AS bootstrap2_js, NULL AS bootstrap2_css FROM read_csv_auto('${url_2023_11_02}') \
UNION SELECT CAST ('2024-03-12' AS DATE) AS crawlDate,*, NULL AS bootstrap2_js, NULL AS bootstrap2_css FROM read_csv_auto('${url_2024_03_12}') \
UNION SELECT CAST ('2024-07-31' AS DATE) AS crawlDate,* FROM read_csv_auto('${url_2024_07_31}')) \
TO '${filename}' (FORMAT 'PARQUET',CODEC 'ZSTD')"

duckdb -c "SET preserve_insertion_order=false; \
COPY (SELECT CAST (ER.crawlDate AS STRING) as crawlDate,\
ER.Codice_IPA, ER.url, ER.lightHouseScore,\
ER.firstMeaningfulPaint, ER.totalByteWeight, \
ER.bootstrap, ER.bootstrapItalia, ER.bootstrap2_js, \
regexp_extract(ER.bootstrap2_css, '\"(.*)\"',1) as bootstrap2_css, \
IPA.Denominazione_ente, IPA.Codice_comune_ISTAT, IPA.Tipologia, \
IPA.Codice_Categoria, IPA.Codice_natura, \
cIPA.Nome_categoria, cIPA.Tipologia_categoria, \
IPA.Codice_ateco, \
entiCheck.HTTPCode, \
CurlExitStatuses.Description as CurlExitStatus \
FROM read_parquet('${filename}') ER \
JOIN read_csv_auto('${url_IPA}') IPA ON ER.Codice_IPA = IPA.Codice_IPA \
JOIN read_csv_auto('${url_categorieIPA}') cIPA ON IPA.Codice_Categoria = cIPA.Codice_categoria \
JOIN read_csv_auto('${url_entiCheck}') entiCheck ON ER.Codice_IPA=entiCheck.Codice_IPA \
LEFT JOIN read_csv_auto('${url_CurlExitStatuses}') CurlExitStatuses ON entiCheck.CurlExitStatus=CurlExitStatuses.CurlExitStatus ) \
TO '${filename2}' (FORMAT 'PARQUET',CODEC 'ZSTD')"

cat "${filename2}"
rm "${filename}" "${filename2}"
