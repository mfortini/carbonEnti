#! /bin/bash

filename=/tmp/entiRes.parquet
filename2=/tmp/entiResIPA.parquet


url_2022_02_11=https://raw.githubusercontent.com/mfortini/carbonEnti/1609f64997c079676c5ebc5adb43494f3ea3cc82/entiRes.csv
url_2023_11_02=https://raw.githubusercontent.com/mfortini/carbonEnti/6101134a9f8c3878f5aa66632ee3dd6330fb9920/entiRes.csv
url_2024_03_12=https://raw.githubusercontent.com/mfortini/carbonEnti/1219211b7024ede7e7ba8727aa93148136ddf1ff/entiRes.csv
url_2024_07_31=https://raw.githubusercontent.com/mfortini/carbonEnti/60ae5d46f44582aae2d8d2802a08d6a504c7974f/entiRes.csv
url_2025_02_20=https://raw.githubusercontent.com/mfortini/carbonEnti/b5f845e63f77466587a8564023a3b80eb98cba29/entiRes.csv
url_2025_09_19=https://raw.githubusercontent.com/mfortini/carbonEnti/b90d2720cfdccdb72ffa066159d279005cb03722/entiRes.csv

url_IPA=https://raw.githubusercontent.com/mfortini/carbonEnti/main/enti.csv
url_categorieIPA=https://raw.githubusercontent.com/mfortini/carbonEnti/main/entiCategorie.csv
url_entiCheck=https://raw.githubusercontent.com/mfortini/carbonEnti/main/entiCheck.csv
url_CurlExitStatuses=https://raw.githubusercontent.com/mfortini/carbonEnti/main/CurlExitStatuses.csv

duckdb -c "SET preserve_insertion_order=false;\
COPY (SELECT CAST ('2022-02-11' AS DATE) AS crawlDate,codice_IPA,url,lighthouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia, NULL AS bootstrap2_js, NULL AS bootstrap2_css FROM read_csv_auto('${url_2022_02_11}') \
UNION SELECT CAST ('2023-11-02' AS DATE) AS crawlDate,codice_IPA,url,lighthouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia, NULL AS bootstrap2_js, NULL AS bootstrap2_css FROM read_csv_auto('${url_2023_11_02}') \
UNION SELECT CAST ('2024-03-12' AS DATE) AS crawlDate,codice_IPA,url,lighthouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia, NULL AS bootstrap2_js, NULL AS bootstrap2_css FROM read_csv_auto('${url_2024_03_12}') \
UNION SELECT CAST ('2024-07-31' AS DATE) AS crawlDate,codice_IPA,url,lighthouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia, bootstrap2_js, regexp_extract(bootstrap2_css, '\"(.*)\"',1) as bootstrap2_css FROM read_csv_auto('${url_2024_07_31}') \
UNION SELECT CAST ('2025-02-20' AS DATE) AS crawlDate, codice_IPA,url,100.*lighthouseScore AS lightHouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia, bootstrap2_js, bootstrap2_css FROM read_csv_auto('${url_2025_02_20}') \
UNION SELECT CAST ('2025-09-19' AS DATE) AS crawlDate, codice_IPA,url,100.*lighthouseScore AS lightHouseScore,firstMeaningfulPaint,totalByteWeight,bootstrap,bootstrapItalia, bootstrap2_js, bootstrap2_css FROM read_csv_auto('${url_2025_09_19}') \
) TO '${filename}' (FORMAT 'PARQUET',CODEC 'ZSTD')"

duckdb -c "SET preserve_insertion_order=false; \
COPY (SELECT CAST (ER.crawlDate AS STRING) as crawlDate,\
ER.Codice_IPA, ER.url, ER.lightHouseScore,\
ER.firstMeaningfulPaint, ER.totalByteWeight, \
ER.bootstrap, ER.bootstrapItalia, ER.bootstrap2_js, \
ER.bootstrap2_css, \
IPA.Denominazione_ente, IPA.Codice_comune_ISTAT, IPA.Tipologia, \
IPA.Codice_Categoria, IPA.Codice_natura, \
cIPA.Nome_categoria, cIPA.Tipologia_categoria, \
IPA.Codice_ateco, \
entiCheck.HTTPCode, \
CurlExitStatuses.Description as CurlExitStatus \
FROM read_parquet('${filename}') ER \
JOIN read_csv_auto('${url_IPA}', strict_mode=false) IPA ON ER.Codice_IPA = IPA.Codice_IPA \
JOIN read_csv_auto('${url_categorieIPA}', strict_mode=false) cIPA ON IPA.Codice_Categoria = cIPA.Codice_categoria \
JOIN read_csv_auto('${url_entiCheck}', strict_mode=false) entiCheck ON ER.Codice_IPA=entiCheck.Codice_IPA \
LEFT JOIN read_csv_auto('${url_CurlExitStatuses}', strict_mode=false) CurlExitStatuses ON entiCheck.CurlExitStatus=CurlExitStatuses.CurlExitStatus ) \
TO '${filename2}' (FORMAT 'PARQUET',CODEC 'ZSTD')"

cat "${filename2}"
rm "${filename}" "${filename2}"
