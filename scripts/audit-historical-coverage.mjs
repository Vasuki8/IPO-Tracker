import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const RECOVERY=path.join(ROOT,"data","recovery");
const MANIFEST=path.join(ROOT,"data","bse-ipo-sources.json");
export function buildHistoricalCoverageAudit(years, recoveryYears, sources){
  return years.map(year=>({
    year,
    recovery_present:recoveryYears.has(year),
    bse_verified_sources:sources.filter(source=>source.year===year).length,
    status:recoveryYears.has(year)?"materialized":"universe_not_materialized"
  }));
}
function run(){
  const recoveryYears=new Set(fs.existsSync(RECOVERY)?fs.readdirSync(RECOVERY,{withFileTypes:true}).filter(x=>x.isDirectory()&&/^20\d{2}$/.test(x.name)).map(x=>Number(x.name)):[]);
  const sources=fs.existsSync(MANIFEST)?JSON.parse(fs.readFileSync(MANIFEST,"utf8")).sources||[]:[];
  console.log(JSON.stringify({historical_coverage:buildHistoricalCoverageAudit([2026,2025,2024,2023,2022,2021,2020],recoveryYears,sources)},null,2));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;if(isMain)run();
