// Usage: node atlas_map.mjs "Japan" 900 900 [10m|50m] [out.svg]
// Prints JSON {name, d, bounds, len}; with out.svg also writes the gold silhouette SVG (viewBox = bounds).
// Prints a JSON {d, w, h} : SVG path of the country fitted in a w×h box.
import { readFileSync, writeFileSync } from 'node:fs';
import { feature } from 'topojson-client';
import { geoPath, geoMercator, geoConicEqualArea } from 'd3-geo';

const [name, W = '900', H = '900', res = '50m', out] = process.argv.slice(2);
const topo = JSON.parse(readFileSync(new URL(`./node_modules/world-atlas/countries-${res}.json`, import.meta.url)));
const all = feature(topo, topo.objects.countries).features;
// Scotland, England, Wales, Northern Ireland are one "United Kingdom" in world-atlas: their own outlines come from
// Natural Earth map units (subunits-50m.json, public domain), whatever resolution is asked.
const SUB = JSON.parse(readFileSync(new URL('./subunits-50m.json', import.meta.url))).features;
const f = SUB.find(c => c.properties.name.toLowerCase() === name.toLowerCase())
  || all.find(c => c.properties.name.toLowerCase() === name.toLowerCase())
  || all.find(c => c.properties.name.toLowerCase().includes(name.toLowerCase()));
if (!f) { console.error('Not found. Names:', all.map(c => c.properties.name).sort().join(', ')); process.exit(1); }

const w = +W, h = +H;
const proj = geoMercator().fitSize([w, h], f);
const path = geoPath(proj);
const d = path(f).replace(/(\d+\.\d)\d+/g, '$1');
const [[x0, y0], [x1, y1]] = path.bounds(f);
console.log(JSON.stringify({ name: f.properties.name, d, bounds: [x0, y0, x1, y1].map(v => Math.round(v)), len: d.length }));
if (out) { const [a, b, c, e] = [x0, y0, x1, y1].map(Math.round); writeFileSync(out, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${a} ${b} ${c - a} ${e - b}" width="${c - a}" height="${e - b}"><path fill="#FECB7A" d="${d}"/></svg>`); }
