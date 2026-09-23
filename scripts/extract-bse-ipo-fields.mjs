import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST_PATH = path.join(ROOT, "data", "bse-ipo-sources.json");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function text(html) {
  return String(html ?? "").replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ")
    .replace(/<[^>]+>/g," ").replace(/&nbsp;/gi," ").replace(/&amp;/gi,"&").replace(/\s+/g," ").trim();
}
function isoDate(raw) {
  if (!raw) return null;
  const parsed = Date.parse(raw);
  if (!Number.isFinite(parsed)) return null;
  return new Date(parsed).toISOString().slice(0, 10);
}
function slug(value) {
  return String(value ?? "").toLowerCase().replace(/&/g," and ").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
}
function number(raw) {
  const value=Number(String(raw??"").replace(/,/g,"").trim());
  return Number.isFinite(value)&&value>0?value:null;
}
export function parseBseEquityIssuePage(html) {
  const body=text(html);
  if (!/Security Type\s+Equity/i.test(body)) return null;
  const grab=(label, pattern)=>{const m=body.match(new RegExp(label+"\\s+"+pattern,"i"));return m?.[1]??null;};
  const period=body.match(/Issue Period\s+(\d{2}\s+[A-Za-z]{3}\s+\d{4})\s+to\s+(\d{2}\s+[A-Za-z]{3}\s+\d{4})/i);
  const band=body.match(/Price Band\s+([0-9,.]+)\s*-\s*([0-9,.]+)/i);
  return {
    symbol: grab("Symbol","([A-Z0-9_-]+)"),
    issue_size_shares: number(grab("Issue Size\\s*[–-]?\\s*No\\. of Shares","([0-9,]+)")),
    price_band: band ? { min:number(band[1]), max:number(band[2]) } : null,
    market_lot: number(grab("Market Lot","([0-9,]+)")),
    minimum_bid_quantity: number(grab("Minimum Bid Quantity","([0-9,]+)")),
    open_date_raw: period?.[1]??null,
    close_date_raw: period?.[2]??null
  };
}
export function parseBseListingNotice(html) {
  const body=text(html);
  const company=body.match(/Subject\s+Listing of Equity Shares of\s+(.+?)\s+Attachments/i)?.[1]??null;
  const effective=body.match(/effective from\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})/i)?.[1]??null;
  const lot=number(body.match(/Market Lot\s+([0-9,]+)/i)?.[1]);
  const price=number(body.match(/Issue Price for the current Public issue\s+Rs\.?\s*([0-9,.]+)/i)?.[1]);
  const segment=body.match(/\bSegment\s+(SME|Equity)\b/i)?.[1]??null;
  const board=segment?.toLowerCase()==="sme" ? "SME" : segment ? "Mainboard" : null;
  return { company, listing_date_raw:effective, market_lot:lot, issue_price:price, board };
}
function sourceEvidence(source, collectedAt) {
  return {
    url: source.url,
    document_type: source.kind === "listing_notice" ? "BSE Listing Notice" : "BSE Public Issue Detail",
    document_identity: (source.kind === "listing_notice" ? "BSE Listing Notice — " : "BSE Public Issue Detail — ") + source.issuer_name,
    publication_date: source.publication_date ?? null,
    collected_at: collectedAt
  };
}
function addDocument(record, evidence) {
  record.documents ??= [];
  if (!record.documents.some((doc) => doc.url === evidence.url)) {
    record.documents.push({
      type: evidence.document_type,
      identity: evidence.document_identity,
      url: evidence.url,
      publication_date: evidence.publication_date,
      collected_at: evidence.collected_at
    });
  }
}
function fill(record, key, value, sourceValue, evidence, conflicts) {
  if (value === null || value === undefined) return false;
  const existing = record[key]?.value;
  if (existing !== null && existing !== undefined) {
    if (JSON.stringify(existing) !== JSON.stringify(value)) conflicts.push({ field:key, existing, bse:value });
    return false;
  }
  record[key] = { value, source_value:sourceValue, status:"verified", page:null, source:evidence };
  return true;
}
export function applyBseParsedFields(record, source, parsed, collectedAt) {
  const conflicts=[]; let changed=false;
  const evidence=sourceEvidence(source,collectedAt);
  if (source.kind === "listing_notice") {
    changed = fill(record,"listing_date",isoDate(parsed.listing_date_raw),parsed.listing_date_raw,evidence,conflicts) || changed;
    changed = fill(record,"issue_price",parsed.issue_price,parsed.issue_price == null ? null : "₹"+parsed.issue_price+" per share",evidence,conflicts) || changed;
    changed = fill(record,"market_lot",parsed.market_lot,parsed.market_lot == null ? null : String(parsed.market_lot),evidence,conflicts) || changed;
  } else {
    const min=parsed.price_band?.min, max=parsed.price_band?.max;
    if (min != null && max != null) changed = fill(record,"price_band",{min,max},min+"-"+max,evidence,conflicts) || changed;
    changed = fill(record,"market_lot",parsed.market_lot,parsed.market_lot == null ? null : String(parsed.market_lot),evidence,conflicts) || changed;
    changed = fill(record,"minimum_bid_quantity",parsed.minimum_bid_quantity,parsed.minimum_bid_quantity == null ? null : String(parsed.minimum_bid_quantity),evidence,conflicts) || changed;
    changed = fill(record,"open_date",isoDate(parsed.open_date_raw),parsed.open_date_raw,evidence,conflicts) || changed;
    changed = fill(record,"close_date",isoDate(parsed.close_date_raw),parsed.close_date_raw,evidence,conflicts) || changed;
  }
  if (changed) {
    addDocument(record,evidence);
    record.last_collected_at=collectedAt;
  }
  return {changed,conflicts};
}
export function buildBseOnlyRecoveryRecord(source, parsed, collectedAt) {
  if (source?.kind !== "listing_notice" || source?.inclusion !== "ipo") return null;
  if (!Number.isInteger(Number(source.year))) return null;
  if (!parsed?.company || slug(parsed.company) !== slug(source.issuer_name)) return null;
  if (!isoDate(parsed.listing_date_raw)) return null;

  const evidence=sourceEvidence(source,collectedAt);
  const record={
    id:slug(source.issuer_name),
    issuer_name:source.issuer_name,
    board:parsed.board??null,
    sector:null,
    status:"listed",
    nse_symbol:null,
    nse_series:null,
    bse_source:{
      url:evidence.url,
      document_type:evidence.document_type,
      document_identity:evidence.document_identity,
      publication_date:evidence.publication_date,
      collected_at:collectedAt
    },
    terms:{
      price_band:null,
      market_lot:null,
      minimum_bid_quantity:null,
      open_date:null,
      close_date:null
    },
    documents:[],
    first_observed_at:collectedAt,
    last_collected_at:collectedAt,
    board_evidence:parsed.board ? [{...evidence,page:null}] : [],
    status_evidence:[{...evidence,page:null}]
  };
  applyBseParsedFields(record,source,parsed,collectedAt);
  return record;
}

function recoveryFileForYear(year) {
  return path.join(RECOVERY_ROOT,String(year),"nse-issue-information.json");
}

function recoveryFiles() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT,{withFileTypes:true}).filter(x=>x.isDirectory()).flatMap(dir=>{
    const p=path.join(RECOVERY_ROOT,dir.name);
    return fs.readdirSync(p).filter(name=>name.endsWith(".json")).map(name=>path.join(p,name));
  });
}
async function fetchPage(url){
  const r=await fetch(url,{headers:{"user-agent":USER_AGENT,"accept":"text/html,*/*","referer":"https://www.bseindia.com/"},signal:AbortSignal.timeout(20000)});
  if(!r.ok) throw new Error("HTTP "+r.status+" "+url); return r.text();
}
async function run(){
  if(!fs.existsSync(MANIFEST_PATH)){console.log(JSON.stringify({bse_detail_stats:{sources:0,parsed:0,applied:0,conflicts:0,errors:0}}));return;}
  const manifest=JSON.parse(fs.readFileSync(MANIFEST_PATH,"utf8"));
  const files=recoveryFiles();
  const loaded=files.map(file=>({file,data:JSON.parse(fs.readFileSync(file,"utf8")),changed:false}));
  const stats={sources:(manifest.sources||[]).length,parsed:0,matched_records:0,created_records:0,applied:0,conflicts:0,errors:0,unmatched_sources:0};
  const now=new Date().toISOString();
  for(const source of manifest.sources||[]){
    try{
      const html=await fetchPage(source.url);
      const parsed=source.kind==="listing_notice"?parseBseListingNotice(html):parseBseEquityIssuePage(html);
      if(!parsed){console.log(JSON.stringify({issuer_name:source.issuer_name,kind:source.kind,url:source.url,parsed:null}));continue;}
      stats.parsed++;
      const candidates=[];
      for(const item of loaded) for(const record of item.data.records||[]) {
        if(slug(record.issuer_name)===slug(source.issuer_name)) candidates.push({item,record});
      }
      if(candidates.length===0){
        const newRecord=buildBseOnlyRecoveryRecord(source,parsed,now);
        if(newRecord){
          const year=Number(source.year);
          let item=loaded.find((entry)=>Number(path.basename(path.dirname(entry.file)))===year);
          if(!item){
            const file=recoveryFileForYear(year);
            item={
              file,
              data:{
                source_family:"Official NSE / SEBI / BSE offer-document and exchange evidence",
                collection_started_at:now,
                generated_at:now,
                records:[]
              },
              changed:false
            };
            loaded.push(item);
          }
          const duplicate=loaded.some((entry)=>entry.data.records?.some((record)=>record.id===newRecord.id));
          if(!duplicate){
            item.data.records??=[];
            item.data.records.push(newRecord);
            item.data.records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
            item.changed=true;
            stats.created_records++;
            stats.applied++;
            console.log(JSON.stringify({issuer_name:source.issuer_name,kind:source.kind,url:source.url,parsed,created:true,conflicts:[]}));
            continue;
          }
        }
        stats.unmatched_sources++;
        console.log(JSON.stringify({issuer_name:source.issuer_name,kind:source.kind,url:source.url,parsed,record_match_count:0}));
        continue;
      }
      if(candidates.length!==1){
        stats.unmatched_sources++;
        console.log(JSON.stringify({issuer_name:source.issuer_name,kind:source.kind,url:source.url,parsed,record_match_count:candidates.length}));
        continue;
      }
      stats.matched_records++;
      const {item,record}=candidates[0];
      const result=applyBseParsedFields(record,source,parsed,now);
      stats.conflicts+=result.conflicts.length;
      if(result.changed){item.changed=true;stats.applied++;}
      console.log(JSON.stringify({issuer_name:source.issuer_name,kind:source.kind,url:source.url,parsed,applied:result.changed,conflicts:result.conflicts}));
    }catch(e){stats.errors++;console.warn("BSE source unavailable for "+source.issuer_name+": "+e.message);}
  }
  for(const item of loaded) if(item.changed){
    item.data.generated_at=now;
    fs.mkdirSync(path.dirname(item.file),{recursive:true});
    fs.writeFileSync(item.file,JSON.stringify(item.data,null,2)+"\n");
  }
  console.log(JSON.stringify({bse_detail_stats:stats},null,2));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;
if(isMain)run().catch(e=>{console.error(e);process.exit(1);});
