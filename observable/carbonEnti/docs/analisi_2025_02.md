---
title: Analisi Lighthouse dei siti delle Pubbliche Amministrazioni italiane (2024-07)
theme: cotton
sql:
    entiRes: ./data/entiRes.parquet
---



# Analisi Lighthouse dei siti delle Pubbliche Amministrazioni italiane

```sql id=[{countEnti}]
SELECT COUNT(Codice_IPA) AS countEnti FROM entiRes WHERE crawlDate= '2025-02-20'
```

Lighthouse è stato fatto girare su tutti i siti delle ${countEnti} Pubbliche Amministrazioni italiane presenti su IndicePA.

## In quanti enti è fallito Lighthouse?

```sql
PIVOT (SELECT CAST (crawlDate AS STRING) as crawlDate, Codice_IPA, CASE WHEN (lighthouseScore = 0 OR lighthouseScore IS NULL) THEN 'KO' ELSE 'OK' END AS LightHouseRun FROM entiRes WHERE crawlDate= '2025-02-20') ON LightHouseRun USING COUNT(Codice_IPA) GROUP BY crawlDate
```

```sql id=LightHouseRun
SELECT COUNT(Codice_IPA) AS countEnti, CASE WHEN (lighthouseScore = 0 OR lighthouseScore IS NULL) THEN 'KO' ELSE 'OK' END AS LightHouseRun FROM entiRes WHERE crawlDate= '2025-02-20' GROUP BY LightHouseRun
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


## Distribuzione dei punteggi lighthouse

```sql id=lightHouseScore
SELECT  CAST (crawlDate AS STRING) as crawlDate, Codice_IPA, Codice_comune_ISTAT, denominazione_ente, url, lightHouseScore, firstMeaningfulPaint, totalByteWeight, bootstrap, bootstrapItalia from entiRes WHERE lightHouseScore > 0 AND lightHouseScore IS NOT NULL AND crawlDate = '2025-02-20'
```

```js
const filterDateScore = "2025-02-20";
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
const filterDateTTFMP = '2025-02-20';
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
const filterDateDim = "2025-02-20";
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
SELECT Nome_categoria, Tipologia_categoria, bootstrap2_css, COUNT(Codice_IPA) countEnti FROM entiRes WHERE lightHouseScore IS NOT NULL AND lightHouseScore > 0 AND crawlDate = '2025-02-20' AND bootstrap2_css IS NOT NULL AND bootstrap2_css != '' GROUP BY Nome_categoria, Tipologia_categoria, bootstrap2_css
```


```sql
PIVOT (SELECT * FROM entiRes WHERE bootstrap2_css IS NOT NULL AND lightHouseScore IS NOT NULL AND bootstrap2_css != '' AND lightHouseScore > 0 AND crawlDate = '2025-02-20' ) ON bootstrap2_css USING COUNT(Codice_IPA) GROUP BY Nome_categoria
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
SELECT Nome_categoria, Tipologia_categoria, bootstrap2_js, COUNT(Codice_IPA) countEnti FROM entiRes WHERE lightHouseScore IS NOT NULL AND lightHouseScore > 0 AND crawlDate = '2025-02-20' AND bootstrap2_js IS NOT NULL AND bootstrap2_js != '' GROUP BY Nome_categoria, Tipologia_categoria, bootstrap2_js
```


```sql
PIVOT (SELECT * FROM entiRes WHERE bootstrap2_js IS NOT NULL AND lightHouseScore IS NOT NULL AND bootstrap2_js != '' AND lightHouseScore > 0 AND crawlDate = '2025-02-20' ) ON bootstrap2_js USING COUNT(Codice_IPA) GROUP BY Nome_categoria
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
SELECT * FROM entiRes WHERE crawlDate = '2025-02-20' ORDER BY lightHouseScore DESC
```

```js 
const comuniGeo=FileAttachment("data/comuniGeo.json").json();
```



```sql id=comuniEntiResBootstrap 

SELECT Codice_comune_ISTAT, sum(CASE WHEN bootstrap2_css IS NOT NULL OR bootstrap2_js IS NOT NULL THEN 1 ELSE 0 END) > 0 AS countbootstrap FROM entiRes WHERE Codice_Categoria =='L6' AND Codice_natura = '2430' AND crawlDate = '2025-02-20' GROUP BY Codice_comune_ISTAT;
```

```js
const comuniBootstrap = new Map(comuniEntiResBootstrap.toArray().map(({Codice_comune_ISTAT, countbootstrap}) => [Codice_comune_ISTAT, countbootstrap]))
```

```sql id=scuoleEntiResBootstrap display

SELECT Codice_comune_ISTAT, sum(CASE WHEN bootstrap2_css IS NOT NULL OR bootstrap2_js IS NOT NULL THEN 1 ELSE 0 END)::integer AS countbootstrap FROM entiRes WHERE Codice_Categoria =='L33' AND crawlDate = '2025-02-20' GROUP BY Codice_comune_ISTAT;
```

```js
const scuoleBootstrap = new Map(scuoleEntiResBootstrap.toArray().map(({Codice_comune_ISTAT, countbootstrap}) => [Codice_comune_ISTAT, countbootstrap]))
```

```js

/**
 * Calculate Jenks Natural Breaks for a dataset
 * @param {Array<number>} data - The array of data values
 * @param {number} numClasses - The number of desired classes
 * @returns {Array<number>} - The array of break values (boundaries for each class)
 */
function jenks(data, numClasses) {
    // Remove duplicates from the data
    const uniqueData = [...new Set(data)];

    // If there are fewer unique values than the number of classes, adjust the number of classes
    if (uniqueData.length < numClasses) {
        numClasses = uniqueData.length;
    }

    // Sort data in ascending order
    uniqueData.sort((a, b) => a - b);

    const dataLength = uniqueData.length;

    // Create matrices for variance and class limits
    const lowerClassLimits = Array(dataLength + 1)
        .fill(0)
        .map(() => Array(numClasses + 1).fill(0));

    const varianceCombinations = Array(dataLength + 1)
        .fill(0)
        .map(() => Array(numClasses + 1).fill(0));

    // Initialize the first column
    for (let i = 1; i <= numClasses; i++) {
        lowerClassLimits[1][i] = 1;
        varianceCombinations[1][i] = 0;
        for (let j = 2; j <= dataLength; j++) {
            varianceCombinations[j][i] = Infinity;
        }
    }

    let variance = 0.0;

    // Iterate over the data to calculate the class breaks
    for (let l = 2; l <= dataLength; l++) {
        let sum = 0.0;
        let sumSquares = 0.0;
        let w = 0;

        for (let m = 1; m <= l; m++) {
            const i3 = l - m + 1;
            const value = uniqueData[i3 - 1];

            w++;
            sum += value;
            sumSquares += value * value;
            variance = sumSquares - (sum * sum) / w;

            if (i3 !== 1) {
                for (let j = 2; j <= numClasses; j++) {
                    if (varianceCombinations[l][j] >= variance + varianceCombinations[i3 - 1][j - 1]) {
                        lowerClassLimits[l][j] = i3;
                        varianceCombinations[l][j] = variance + varianceCombinations[i3 - 1][j - 1];
                    }
                }
            }
        }
        lowerClassLimits[l][1] = 1;
        varianceCombinations[l][1] = variance;
    }

    const breaks = Array(numClasses + 1).fill(0);
    breaks[numClasses] = uniqueData[dataLength - 1];
    breaks[0] = uniqueData[0];

    let k = dataLength;
    for (let j = numClasses; j >= 2; j--) {
        const id = lowerClassLimits[k][j] - 1;
        if (id < 0) {
            break; // Prevent out of bounds error
        }
        breaks[j - 1] = uniqueData[id];
        k = lowerClassLimits[k][j] - 1;
    }

    return breaks;
}


// Specify number of desired classes (breaks)
const numClasses = 6;

// Compute the natural breaks
const breaks = jenks(Array.from(scuoleBootstrap.values()), numClasses);


resize((width) =>
Plot.plot({
  height:width,
color: {legend:true},   
      
  marks: [
    Plot.geo(comuniGeo, 
         { fill:  (d) => scuoleBootstrap.get(d.properties.PRO_COM_T)??0}, // Fill color depends on bootstrap value
    {stroke: "black"
    }
    ) // Add county boundaries using the geo mark 
  ]
}))
```

```js

const colors=[
  '#7abdff',
'#66abf5',
'#519aeb',
'#3d88e1',
'#2677d7',
'#0066cc'];

function getColorForValue(value, breaks, default_color) {
    for (let i = 0; i < breaks.length - 1; i++) {
        if (value >= breaks[i] && value <= breaks[i + 1]) {
            return colors[i];
        }
    }
    return default_color; // Default to default class color
}
```


## Mappa dei comuni che usano Bootstrap Italia


```sql id=comuniEntiResBootstrapItalia

SELECT Codice_comune_ISTAT, sum(CASE WHEN bootstrap2_css IS NOT NULL OR bootstrap2_js IS NOT NULL THEN 1 ELSE 0 END) > 0 AS countbootstrap FROM entiRes WHERE Codice_Categoria =='L6' AND Codice_natura = '2430' AND crawlDate = '2025-02-20' GROUP BY Codice_comune_ISTAT;
```

```js
const comuniBootstrapItalia = new Map(comuniEntiResBootstrapItalia.toArray().map(({Codice_comune_ISTAT, countbootstrap}) => [Codice_comune_ISTAT, countbootstrap]))
```


```js
resize((width) =>
Plot.plot({
  height:width,
color: {legend:true,type:"categorical",   
      domain: [true,false],
      range:["blue","lightgrey"]},
  marks: [
    Plot.geo(comuniGeo, 
         { fill:  (d) => comuniBootstrapItalia.get(d.properties.PRO_COM_T)??false}, // Fill color depends on bootstrap value
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
        switch (comuniBootstrapItalia.get(feature.properties.PRO_COM_T)) {
            case true: return {weight:1, opacity:1, fillOpacity:0.9, color: "blue"};
            default:   return {weight:1, opacity:1,fillOpacity:0.9, color: "lightgrey"};
        }
    }
}).addTo(map);
```

## Mappa delle scuole che usano Bootstrap Italia

```sql id=scuoleEntiResBootstrap_Italia display

SELECT Codice_comune_ISTAT, sum(CASE WHEN bootstrap2_css IS NOT NULL OR bootstrap2_js IS NOT NULL THEN 1 ELSE 0 END)::integer AS countbootstrap FROM entiRes WHERE Codice_Categoria =='L33' AND crawlDate = '2025-02-20' GROUP BY Codice_comune_ISTAT;
```

```js
const scuoleBootstrap_Italia = new Map(scuoleEntiResBootstrap_Italia.toArray().map(({Codice_comune_ISTAT, countbootstrap}) => [Codice_comune_ISTAT, countbootstrap]))
```

```js


// Compute the natural breaks
const breaks_scuole_BI = jenks(Array.from(scuoleBootstrap_Italia.values()), numClasses);


resize((width) =>
Plot.plot({
  height:width,
color: {legend:true},   
      
  marks: [
    Plot.geo(comuniGeo, 
         { fill:  (d) => scuoleBootstrap_Italia.get(d.properties.PRO_COM_T)??0}, // Fill color depends on bootstrap value
    {stroke: "black"
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


const colors=[
  '#7abdff',
'#66abf5',
'#519aeb',
'#3d88e1',
'#2677d7',
'#0066cc'];


L.geoJSON(comuniGeo.features, 
{
    style: function(feature) {
        return {weight:0.5, opacity:1, fillOpacity:0.9, fillColor: getColorForValue(scuoleBootstrap_Italia.get(feature.properties.PRO_COM_T),breaks, "lightgrey")};
        }
}).addTo(map);
```




## Mappa dei comuni che usano bootstrap versione ${comuni_filterbootstrap_css}

```sql id=comuni_bootstrap2_css
SELECT Codice_comune_ISTAT, bootstrap2_css FROM entiRes WHERE Codice_Categoria =='L6' AND Codice_natura = '2430' AND crawlDate = '2025-02-20' AND bootstrap2_css IS NOT NULL AND bootstrap2_css != '' ;
```

```js
const comuni_filterbootstrap_css = view(Inputs.select(comuni_bootstrap2_css.toArray().map(x=>x["bootstrap2_css"]), {sort: "ascending", reverse:false, unique: true, label:"Bootstrap version"}));
```

```sql id=comuni_bootstrap2_css_filtered
SELECT Codice_comune_ISTAT, bootstrap2_css FROM entiRes WHERE Codice_Categoria =='L6' AND Codice_natura = '2430' AND crawlDate = '2025-02-20' AND bootstrap2_css = ${comuni_filterbootstrap_css} ;
```


```js
const comuniBootstrap_css = new Map(comuni_bootstrap2_css_filtered.toArray().map(({Codice_comune_ISTAT}) => [Codice_comune_ISTAT, true]))
```

```js
resize((width) =>
Plot.plot({
  height:width,
color: {legend:true,type:"categorical",   
      domain: [true,false],
      range:["blue","lightgrey"]},
  marks: [
    Plot.geo(comuniGeo, 
         { fill:  (d) => comuniBootstrap_css.get(d.properties.PRO_COM_T)??false}, // Fill color depends on bootstrap value
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
        switch (comuniBootstrap_css.get(feature.properties.PRO_COM_T)) {
            case true: return {weight:1, opacity:1, fillOpacity:0.9, color: "blue"};
            default:   return {weight:1, opacity:1,fillOpacity:0.9, color: "lightgrey"};
        }
    }
}).addTo(map);
```


## Mappa delle scuole che usano bootstrap versione ${scuole_filterbootstrap_css}

```sql id=scuole_bootstrap2_css display
SELECT Codice_comune_ISTAT, bootstrap2_css, COUNT(Codice_comune_ISTAT) AS countBootstrap FROM entiRes WHERE Codice_Categoria =='L33' AND crawlDate = '2025-02-20' AND bootstrap2_css IS NOT NULL AND bootstrap2_css != '' GROUP BY Codice_comune_ISTAT, bootstrap2_css HAVING countBootstrap > 0;
```

```js
const scuole_filterbootstrap_css = view(Inputs.select(scuole_bootstrap2_css.toArray().map(x=>x["bootstrap2_css"]), {sort: "ascending", reverse:false, unique: true, label:"Bootstrap version"}));
```

```sql id=scuole_bootstrap2_css_filtered 
SELECT Codice_comune_ISTAT, bootstrap2_css, COUNT(Codice_comune_ISTAT) AS countBootstrap FROM entiRes WHERE Codice_Categoria =='L33' AND crawlDate = '2025-02-20' AND bootstrap2_css == ${scuole_filterbootstrap_css} GROUP BY Codice_comune_ISTAT, bootstrap2_css; ;
```


```js
const scuoleBootstrap_css = new Map(scuole_bootstrap2_css_filtered.toArray().map(({Codice_comune_ISTAT,countBootstrap}) => [Codice_comune_ISTAT, countBootstrap]))
```

```js



// Specify number of desired classes (breaks)
const scuole_css_numClasses = 6;

// Compute the natural breaks
const scuole_css_breaks = jenks(Array.from(scuoleBootstrap_css.values()), scuole_css_numClasses);

console.log("Breaks",scuole_css_breaks);

resize((width) =>
Plot.plot({
  height:width,
color: {legend:true},   
      
  marks: [
    Plot.geo(comuniGeo, 
         { fill:  (d) => scuoleBootstrap_css.get(d.properties.PRO_COM_T)??0}, // Fill color depends on bootstrap value
    {stroke: "black"
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

const colors=[
  '#7abdff',
'#66abf5',
'#519aeb',
'#3d88e1',
'#2677d7',
'#0066cc'];

L.geoJSON(comuniGeo.features, 
{
    style: function(feature) {
        return {weight:0.5, opacity:1, fillOpacity:0.9, fillColor: getColorForValue(scuoleBootstrap_css.get(feature.properties.PRO_COM_T),scuole_css_breaks, "lightgrey")};
        }
}).addTo(map);
```