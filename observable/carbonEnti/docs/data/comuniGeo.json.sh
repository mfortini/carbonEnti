#! /bin/bash

filename=/tmp/comuniGeo.json

ogr2ogr -s_srs "./docs/data/Limiti01012024_g/Com01012024_g/Com01012024_g_WGS84.prj" -t_srs epsg:4326 ${filename}  -f "GeoJSON" "./docs/data/Limiti01012024_g/Com01012024_g/Com01012024_g_WGS84.shp"


cat ${filename}
rm ${filename}