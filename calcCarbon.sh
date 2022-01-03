nomeEnte="$1"
urlEnte="${2#https:\/\/}"
urlEnte="${urlEnte#http:\/\/}"
urlEnte="https://${urlEnte}"

#echo nomeEnte ${nomeEnte} urlEnte ${urlEnte}

node carbon.js "${urlEnte}" | jq -cMS ". | { nomeEnte: \"${nomeEnte}\", lighthouse: .}"
