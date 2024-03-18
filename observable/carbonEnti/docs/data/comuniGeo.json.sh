#! /bin/bash

filename=/tmp/comuniGeo.json

ogr2ogr -s_srs "./docs/data/Limiti01012023_g/Com01012023_g/Com01012023_g_WGS84.prj" -t_srs epsg:4326 ${filename} "./docs/data/Limiti01012023_g/Com01012023_g/Com01012023_g_WGS84.shp"


cat ${filename}
rm ${filename}