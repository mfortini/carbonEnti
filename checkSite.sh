Codice_IPA="$1"
urlEnte="${2#https:\/\/}"
urlEnte="${urlEnte#http:\/\/}"
urlEnte="${2}"


HTTP=$(curl -I -s -o /dev/null -w "%{http_code}" "${urlEnte}")
CURL_EXIT=$?

echo ${Codice_IPA},${HTTP},${CURL_EXIT}
