---
title: Analisi Lighthouse dei siti delle Pubbliche Amministrazioni italiane (2024-07)
theme: cotton
sql:
    entiRes: ./data/entiRes.parquet
---

# Analisi Lighthouse dei siti delle Pubbliche Amministrazioni italiane

```sql id=[{countEnti}]
SELECT COUNT(Codice_IPA) AS countEnti FROM entiRes WHERE crawlDate= '2024-07-31'
```

Lighthouse è stato fatto girare su tutti i siti delle ${countEnti} Pubbliche Amministrazioni italiane presenti su IndicePA.

## In quanti enti è fallito Lighthouse?

```sql
PIVOT (SELECT CAST (crawlDate AS STRING) as crawlDate, Codice_IPA, CASE WHEN (lighthouseScore = 0 OR lighthouseScore IS NULL) THEN 'KO' ELSE 'OK' END AS LightHouseRun FROM entiRes WHERE crawlDate= '2024-07-31') ON LightHouseRun USING COUNT(Codice_IPA) GROUP BY crawlDate
```

```sql id=LightHouseRun
SELECT COUNT(Codice_IPA) AS countEnti, CASE WHEN (lighthouseScore = 0 OR lighthouseScore IS NULL) THEN 'KO' ELSE 'OK' END AS LightHouseRun FROM entiRes WHERE crawlDate= '2024-07-31' GROUP BY LightHouseRun
```

```js
Plot.plot (
    {
      width: width,
      marginLeft: 50, 
        x:{type:"band"},
          color: {legend: true, type:"ordinal",scheme: "Observable10"},
marks: [
    Plot.barY(LightHouseRun,{x: "LightHouseRun", y: "countEnti",fill:"LightHouseRun"}),
    Plot.ruleY([0])
    ]
}
)
```


Alcuni motivi per il fallimento di Lighthouse:

* L'URI è sbagliata
* Il sito non è contattabile
* Il sito ha dei problemi di certificato
* La pagina ha degli errori


### Test con cURL

Per analizzare questi motivi, si è utilizzato cURL con un timeout di 10s e al massimo 2 tentativi per ciascun sito.

```sql 
SELECT CurlExitStatus,COUNT(Codice_IPA) AS countEnti FROM entiRes WHERE crawlDate= '2024-07-31' GROUP BY CurlExitStatus order by countEnti DESC
```


## Quanti hanno risposto in HTTPS?

Alcuni siti dichiarano ancora un'URL con il prefisso `http://` anziché `https://`, non permettendo una connessione sicura.


```sql
PIVOT (SELECT * FROM entiRes WHERE crawlDate = '2024-07-31')  ON starts_with(url, 'https://') USING COUNT(Codice_IPA) GROUP BY crawlDate
```

```sql id=https
SELECT COUNT(Codice_IPA) AS numHTTPS, starts_with(url, 'https://') AS HTTPSresp FROM entiRes WHERE crawlDate = '2024-07-31' AND lightHouseScore IS NOT NULL AND lightHouseScore != 0 GROUP BY HTTPSresp
```

```js
Plot.plot (
    {
      width: width,
      marginLeft: 50, 
        x:{type:"band"},
          color: {legend: true, type:"ordinal",scheme: "Observable10"},
marks: [
    Plot.barY(https,{x: "HTTPSresp", y: "numHTTPS",fill:"HTTPSresp"}),
    Plot.ruleY([0])
    ]
}
)
```

## Distribuzione dei punteggi lighthouse

```sql id=lightHouseScore
SELECT  CAST (crawlDate AS STRING) as crawlDate, Codice_IPA, Codice_comune_ISTAT, denominazione_ente, url, lightHouseScore, firstMeaningfulPaint, totalByteWeight, bootstrap, bootstrapItalia from entiRes WHERE lightHouseScore > 0 AND lightHouseScore IS NOT NULL AND crawlDate = '2024-07-31'
```

```js
const filterDateScore = "2024-07-31";
```

```js
Plot.plot({
  marginLeft: 50, 
  width: width,
  title: `Distribuzione dei punteggi Lighthouse (data crawl ${filterDateScore})`,
  y: {grid: true},
  marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.crawlDate == filterDateScore)), Plot.binX({y: "count"}, {x: "lighthouseScore",fill:"crawlDate"})),
    Plot.ruleY([0])
  ]
})
```

## Tempo necessario per avere un contenuto "significativo"

```js
Plot.plot({
 title: `Distribuzione dei tempi`,
 width: width,
 marginLeft: 50, 
  y: {
    grid: true
  },
  x: { type: "band"},
      color: {legend: false,type:"categorical",scheme: "Observable10"},

  marks: [
    Plot.boxY(lightHouseScore, {x: "crawlDate", y: "firstMeaningfulPaint", fill:"crawlDate"})
  ]
})
```

```js
Plot.plot({
 title: `Distribuzione dei tempi (meno di 9000ms)`,
 width: width,
 marginLeft: 50, 
  y: {
    grid: true
  },
  x: { type: "band"},
        color: {legend: false,type:"categorical",scheme: "Observable10"},

  marks: [
    Plot.boxY(lightHouseScore.toArray().filter((x)=>x.firstMeaningfulPaint < 9000), {x: "crawlDate", y: "firstMeaningfulPaint",fill:"crawlDate"})
  ]
})
```

```js
const filterDateTTFMP = '2024-07-31';
```

```js
Plot.plot({
  title: `Distribuzione dei tempi (meno di 9000ms - data crawl ${filterDateTTFMP})`,
  width: width,
  y: {grid: true},
  color: {legend: true,type:"categorical",scheme: "Observable10"},
  marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.firstMeaningfulPaint < 9000) && (x.crawlDate == filterDateTTFMP)), Plot.binX({y: "count"}, {x: "firstMeaningfulPaint",fill:"crawlDate"})),
    Plot.ruleY([0])
  ]
})
```

## Dimensione della pagina (byte)

```js
Plot.plot({
 title: `Distribuzione della dimensione della pagina`,
 width: width,
 marginLeft: 50, 
  y: {
    grid: true,
    tickFormat: "e"
  },
  x: { type: "band",inset:10},
      color: {legend: false,type:"categorical",scheme: "Observable10"},

  marks: [
    Plot.boxY(lightHouseScore, {x: "crawlDate", y: "totalByteWeight", fill:"crawlDate"})
  ]
})
```

```js
Plot.plot({
 title: `Distribuzione della dimensione della pagina (meno di 10e6 byte)`,
 width: width,
 marginLeft: 50, 
  y: {
    grid: true,
        tickFormat: "e"
  },
  x: { type: "band",inset:1},
        color: {legend: false,type:"ordinal",scheme: "Observable10"},

  marks: [
    Plot.boxY(lightHouseScore.toArray().filter((x)=>x.totalByteWeight < 10e6), {x: "crawlDate", y: "totalByteWeight",fill:"crawlDate", mixBlendMode: "multiply"})
  ]
})
```


```js
const filterDateDim = "2024-07-31";
```

```js
Plot.plot({
 title: `Distribuzione della dimensione della pagina (meno di 10e6 byte - data crawl ${filterDateDim})`,
     width: width,
  y: {grid: true},
  x: {tickFormat:"e"},
    marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.totalByteWeight < 10e6) && (x.crawlDate == filterDateDim)), Plot.binX({y: "count"}, {x: "totalByteWeight",fill:"crawlDate"})),
    Plot.ruleY([0])
  ]
})
```
## Versioni di Bootstrap

### Utilizzando la query CSS

```sql id=bootstrap2_css
SELECT Nome_categoria, Tipologia_categoria, bootstrap2_css, COUNT(Codice_IPA) countEnti FROM entiRes WHERE bootstrap != 'Error' AND lightHouseScore IS NOT NULL AND lightHouseScore > 0 AND crawlDate = '2024-07-31' AND bootstrap2_css IS NOT NULL AND bootstrap2_css != '' GROUP BY Nome_categoria, Tipologia_categoria, bootstrap2_css
```


```sql
PIVOT (SELECT * FROM entiRes WHERE bootstrap2_css IS NOT NULL AND lightHouseScore IS NOT NULL AND bootstrap2_css != '' AND lightHouseScore > 0 AND crawlDate = '2024-07-31' ) ON bootstrap2_css USING COUNT(Codice_IPA) GROUP BY Nome_categoria
```

```js
const filterbootstrap_css = view(Inputs.select(bootstrap2_css.toArray().map(x=>x["Nome_categoria"]), {sort: "ascending", reverse:false, unique: true, label:"Categoria ente"}));
```

```js
Plot.plot (
    {
      title: `Distribuzione delle versioni di Bootstrap tramite query CSS (${filterbootstrap_css})`,
      width: width,
      marginLeft: 50, 
        x:{type:"band"},
          color: {legend: true, type:"ordinal",scheme: "Observable10"},
marks: [
    Plot.barY(bootstrap2_css.toArray().filter((x)=>(x.Nome_categoria == filterbootstrap_css)),{x: "bootstrap2_css", y: "countEnti",fill:"bootstrap2_css"}),
    Plot.ruleY([0])
    ]
}
)
```

### Utilizzando la query JS

```sql id=bootstrap2_js
SELECT Nome_categoria, Tipologia_categoria, bootstrap2_js, COUNT(Codice_IPA) countEnti FROM entiRes WHERE bootstrap != 'Error' AND lightHouseScore IS NOT NULL AND lightHouseScore > 0 AND crawlDate = '2024-07-31' AND bootstrap2_js IS NOT NULL AND bootstrap2_js != '' GROUP BY Nome_categoria, Tipologia_categoria, bootstrap2_js
```


```sql
PIVOT (SELECT * FROM entiRes WHERE bootstrap2_js IS NOT NULL AND lightHouseScore IS NOT NULL AND bootstrap2_js != '' AND lightHouseScore > 0 AND crawlDate = '2024-07-31' ) ON bootstrap2_js USING COUNT(Codice_IPA) GROUP BY Nome_categoria
```

```js
const filterbootstrap_js = view(Inputs.select(bootstrap2_js.toArray().map(x=>x["Nome_categoria"]), {sort: "ascending", reverse:false, unique: true, label:"Categoria ente"}));
```

```js
Plot.plot (
    {
      title: `Distribuzione delle versioni di Bootstrap tramite query JS (${filterbootstrap_js})`,
      width: width,
      marginLeft: 50, 
        x:{type:"band"},
          color: {legend: true, type:"ordinal",scheme: "Observable10"},
marks: [
    Plot.barY(bootstrap2_js.toArray().filter((x)=>(x.Nome_categoria == filterbootstrap_js)),{x: "bootstrap2_js", y: "countEnti",fill:"bootstrap2_js"}),
    Plot.ruleY([0])
    ]
}
)
```



## Tutti i punteggi


```sql
SELECT * FROM entiRes WHERE crawlDate = '2024-07-31' ORDER BY lightHouseScore DESC
```

```js 
const comuniGeo=FileAttachment("data/comuniGeo.json").json();
```



```sql id=comuniEntiResBootstrap 

SELECT Codice_comune_ISTAT, sum(CASE WHEN bootstrap == 'true' THEN 1 ELSE 0 END) > 0 AS countbootstrap FROM entiRes WHERE Codice_Categoria =='L6' AND Codice_natura = '2430'  GROUP BY Codice_comune_ISTAT HAVING countbootstrap == true AND countbootstrap IS NOT NULL;
```

```js
const entiBootstrap = new Map(comuniEntiResBootstrap.toArray().map(({Codice_comune_ISTAT, countbootstrap}) => [Codice_comune_ISTAT, countbootstrap]))
```


## Mappa dei comuni che usano Bootstrap


```js
var filteredComuniGeo=JSON.parse(JSON.stringify(comuniGeo));

filteredComuniGeo.features = filteredComuniGeo.features.filter(comune => entiBootstrap.get(comune.properties.PRO_COM_T));
```


```js
resize((width) =>
Plot.plot({
  height:width,
color: {legend:true,type:"categorical",   
      domain: [true,false],
      range:["blue","grey"]},
  marks: [
    Plot.geo(comuniGeo, 
         { fill:  (d) => entiBootstrap.get(d.properties.PRO_COM_T)??false}, // Fill color depends on bootstrap value
    {stroke: "black",
    }
    ) // Add county boundaries using the geo mark 
  ]
}))
```

```js
const div = display(document.createElement("div"));
div.style = "height: 1200px;";

const map = L.map(div)
  .setView([42.52379,12.21680], 7);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})
  .addTo(map);


L.geoJSON(comuniGeo.features, 
{
    style: function(feature) {
        switch (entiBootstrap.get(feature.properties.PRO_COM_T)) {
            case true: return {weight:1, opacity:1, fillOpacity:1, color: "blue"};
            default:   return {weight:1, opacity:1,fillOpacity:1, color: "grey"};
        }
    }
}).addTo(map);
```


```js
const div = display(document.createElement("div"));
div.style = "height: 400px;";

const map = L.map(div)
  .setView([42.52379,12.21680], 5);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})
  .addTo(map);


L.geoJSON(comuniGeo.features, 
{
    style: function(feature) {
        switch (comuniBootstrap.get(feature.properties.PRO_COM_T)) {
            case "true": return {weight:1, opacity:1, fillOpacity:0.7, color: "#ff0000"};
            case "false":   return {weight:1, opacity:1,fillOpacity:0.7, color: "#0000ff"};
            default:   return {weight:1, opacity:1,fillOpacity:0.7, color: "#111111"};
        }
    }
}).addTo(map);
```

## Mappa dei comuni che usano Bootstrap Italia

```js
const comuniBootstrapItalia = new Map(lightHouseScore.toArray().map(({Codice_comune_ISTAT, bootstrapItalia}) => [Codice_comune_ISTAT, bootstrapItalia]))
```


```js
resize((width) =>
Plot.plot({
  width,
  height:width,
color: {legend:true,type:"categorical"},
  marks: [
    Plot.geo(comuniGeo, 
         { fill: (d) => comuniBootstrapItalia.get(d.properties.PRO_COM_T) }, // Fill color depends on bootstrap value
    {stroke: "black"}
    ) // Add county boundaries using the geo mark 
  ]
}))
```

```js
const div = display(document.createElement("div"));
div.style = "height: 400px;";

const map = L.map(div)
  .setView([42.52379,12.21680], 5);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})
  .addTo(map);


L.geoJSON(comuniGeo.features, 
{
    style: function(feature) {
        switch (comuniBootstrapItalia.get(feature.properties.PRO_COM_T)) {
            case true: return {weight:1, opacity:1, fillOpacity:0.7, color: "#ff0000"};
            case false:   return {weight:1, opacity:1,fillOpacity:0.7, color: "#0000ff"};
            default:   return {weight:1, opacity:1,fillOpacity:0.7, color: "#111111"};
        }
    }
}).addTo(map);
```
