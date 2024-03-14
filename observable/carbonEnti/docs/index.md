---
title: Analisi Lighthouse dei siti dei comuni italiani
theme: cotton
sql:
    entiRes: ./data/entiRes.parquet
---


# Analisi Lighthouse dei siti dei comuni italiani

Lighthouse è stato fatto girare su tutti i siti dei comuni italiani presenti su IndicePA.

## In quanti enti è fallito Lighthouse?

```sql
SELECT CAST (crawlDate AS STRING) as crawlDate, COUNT(Codice_IPA) FROM entiRes where lighthouseScore = 0 GROUP BY crawlDate ORDER BY crawlDate
```

## Quanti hanno risposto in HTTPS?


```sql
PIVOT entiRes  ON starts_with(url, 'https://') USING COUNT(Codice_IPA) GROUP BY crawlDate
```

```sql id=https
SELECT CAST (crawlDate AS STRING) as crawlDate, COUNT(Codice_IPA) numHTTPS FROM entiRes WHERE  starts_with(url, 'https://') GROUP BY crawlDate ORDER BY crawlDate
```

```js
Plot.plot (
    {
        x:{type:"band"},
          color: {legend: true, type:"ordinal",scheme: "Observable10"},
marks: [
    Plot.barY(https,{x: "crawlDate", y: "numHTTPS",fill:"crawlDate"}),
    Plot.ruleY([0])
    ]
}
)
```

## Distribuzione dei punteggi lighthouse

```sql id=lightHouseScore
SELECT  CAST (crawlDate AS STRING) as crawlDate, Codice_IPA, denominazione_ente, url, lightHouseScore, firstMeaningfulPaint, totalByteWeight, bootstrap, bootstrapItalia from entiRes WHERE lightHouseScore > 0
```

```js
Plot.plot({
 title: `Distribuzione dei punteggi Lighthouse`,
   color: {legend: true,type:"ordinal",scheme: "Observable10"},
  y: {
    grid: true,
    inset: 10
  },
  x: {
        type: "band",
  },
  marks: [
    Plot.boxY(lightHouseScore, {x: "crawlDate", y: "lighthouseScore",fill:"crawlDate"})
  ]
})
```

```js
const filterDateScore = view(Inputs.select(lightHouseScore.toArray().map(x=>x["crawlDate"]), {sort: "descending", reverse:true, unique: true, label:"Data di crawl"}));
```

```js
Plot.plot({
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
const filterDateTTFMP = view(Inputs.select(lightHouseScore.toArray().map(x=>x["crawlDate"]), {sort: "descending", reverse:true, unique: true, label:"Data di crawl"}));
```

```js
Plot.plot({
  title: `Distribuzione dei tempi (meno di 9000ms - data crawl ${filterDateTTFMP})`,
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
const filterDateDim = view(Inputs.select(lightHouseScore.toArray().map(x=>x["crawlDate"]), {sort: "descending", reverse:true, unique: true, label:"Data di crawl"}));
```

```js
Plot.plot({
 title: `Distribuzione della dimensione della pagina (meno di 10e6 byte - data crawl ${filterDateDim})`,
  y: {grid: true},
  x: {tickFormat:"e"},
    marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.totalByteWeight < 10e6) && (x.crawlDate == filterDateDim)), Plot.binX({y: "count"}, {x: "totalByteWeight",fill:"crawlDate"})),
    Plot.ruleY([0])
  ]
})
```


## Uso di Bootstrap

```sql
PIVOT (SELECT * FROM entiRes WHERE bootstrap != 'Error') ON bootstrap USING COUNT(Codice_IPA) GROUP BY crawlDate
```

### Uso di Bootstrap Italia (fra chi usa Bootstrap)

```sql
PIVOT (SELECT * FROM entiRes WHERE bootstrap = 'true') ON bootstrapItalia USING COUNT(Codice_IPA) GROUP BY crawlDate
```

```js
const filterDateBootstrap = view(Inputs.select(lightHouseScore.toArray().map(x=>x["crawlDate"]), {sort: "descending", reverse:true, unique: true, label:"Data di crawl"}));
```
<div class="grid grid-cols-2">
<div class="card">

### Bootstrap

```js
resize((width) =>
Plot.plot({
  title: `Distribuzione dei tempi con Bootstrap (data crawl ${filterDateBootstrap})`,
  y: {grid: true},
  width,
  color: {legend: true,type:"categorical",scheme: "Observable10"},
  marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.firstMeaningfulPaint < 9000) && (x.bootstrap == 'true') && (x.crawlDate == filterDateBootstrap)), Plot.binX({y: "count"}, {x: "firstMeaningfulPaint",fill:d3.schemeObservable10[0]})),
    Plot.ruleY([0])
  ]
}))
```

```js
resize((width) =>
Plot.plot({
  title: `Distribuzione dei tempi senza Bootstrap (data crawl ${filterDateBootstrap})`,
  y: {grid: true},
  width,
  color: {legend: true,type:"categorical",scheme: "Observable10"},
  marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.firstMeaningfulPaint < 9000) && (x.bootstrap == 'false') && (x.crawlDate == filterDateBootstrap)), Plot.binX({y: "count"}, {x: "firstMeaningfulPaint",fill:d3.schemeObservable10[1]})),
    Plot.ruleY([0])
  ]
}))
```


</div>
<div class="card">

### Bootstrap Italia

```js
resize((width) =>
Plot.plot({
  title: `Distribuzione dei tempi con Bootstrap Italia (data crawl ${filterDateBootstrap})`,
  y: {grid: true},
  width,
  color: {legend: true,type:"categorical",scheme: "Observable10"},
  marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.firstMeaningfulPaint < 9000) && (x.bootstrapItalia == true) && (x.crawlDate == filterDateBootstrap)), Plot.binX({y: "count"}, {x: "firstMeaningfulPaint",fill:d3.schemeObservable10[0]})),
    Plot.ruleY([0])
  ]
}))
```

```js
resize((width) =>
Plot.plot({
  title: `Distribuzione dei tempi senza Bootstrap Italia (data crawl ${filterDateBootstrap})`,
  y: {grid: true},
  width,
  color: {legend: true,type:"categorical",scheme: "Observable10"},
  marks: [
    Plot.rectY(lightHouseScore.toArray().filter((x)=>(x.firstMeaningfulPaint < 9000) && (x.bootstrapItalia == false) && (x.crawlDate == filterDateBootstrap)), Plot.binX({y: "count"}, {x: "firstMeaningfulPaint",fill:d3.schemeObservable10[1]})),
    Plot.ruleY([0])
  ]
}))
```

</div>
</div>


## Tutti i punteggi

```js
const filterDateTable = view(Inputs.select(lightHouseScore.toArray().map(x=>x["crawlDate"]), {sort: "descending", reverse:true, unique: true, label:"Data di crawl"}));
```

```sql
SELECT * FROM entiRes WHERE crawlDate = ${filterDateTable} ORDER BY lightHouseScore DESC
```
