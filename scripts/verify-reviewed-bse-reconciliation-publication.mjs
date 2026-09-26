import fs from "node:fs";
import path from "node:path";
import {fileURLToPath,pathToFileURL} from "node:url";
import {
  AUDIT_PATH,MANIFEST_PATH,RECEIPT_PATH,REVIEW_PATH,
  applyReviewedBseReconciliation,loadRecovery
} from "./apply-reviewed-bse-reconciliation.mjs";
import {fetchPublishedSnapshot,LIVE_DATA_URL} from "./verify-bse-publication.mjs";
import {hash} from "./apply-reviewed-nse-ipos.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const EXPECTED={
  "computer-age-management-services-limited":{issuer:"Computer Age Management Services Limited",listing:"2020-10-01",price:1230,open:"2020-09-21",close:"2020-09-23"},
  "protean-egov-technologies-limited":{issuer:"Protean eGov Technologies Limited",listing:"2023-11-13",price:792,open:"2023-11-06",close:"2023-11-08",minBid:18},
  "fabtech-technologies-limited":{issuer:"Fabtech Technologies Limited",listing:"2025-10-07",price:191,open:"2025-09-29",close:"2025-10-01",minBid:75},
  "happy-forging-limited":{issuer:"Happy Forgings Limited",listing:"2023-12-27"},
  "kronox-lab-scienceslimited":{issuer:"Kronox Lab Sciences Limited",listing:"2024-06-10"}
};
const value=(r,f)=>r?.[f]?.value??null;

export function auditBseReconciliationPublication({manifest,review,receipt,reviewBytes,audit,recovery,data,checkedAt}){
  if(data?.schema_version!=="1.2.0"||!Array.isArray(data.records)||!Number.isFinite(Date.parse(checkedAt)))throw new Error("invalid_public_snapshot");
  const plan=applyReviewedBseReconciliation(recovery,data,manifest,review,receipt,reviewBytes,audit);
  if(plan.stats.moved||plan.stats.added||plan.stats.renamed)throw new Error("reviewed_bse_reconciliation_not_in_recovery");

  const results=[];
  for(const [id,expected] of Object.entries(EXPECTED)){
    const hits=data.records.filter(r=>r.id===id);
    const live=hits.length===1?hits[0]:null;
    const errors=[];
    if(!live||live.issuer_name!==expected.issuer||live.status!=="listed")errors.push("identity_status");
    if(value(live,"listing_date")!==expected.listing)errors.push("listing_date");
    if(expected.price!=null&&value(live,"issue_price")!==expected.price)errors.push("issue_price");
    if(expected.open!=null&&value(live,"open_date")!==expected.open)errors.push("open_date");
    if(expected.close!=null&&value(live,"close_date")!==expected.close)errors.push("close_date");
    if(expected.minBid!=null&&value(live,"minimum_bid_quantity")!==expected.minBid)errors.push("minimum_bid_quantity");
    if(["computer-age-management-services-limited","protean-egov-technologies-limited"].includes(id)){
      if(!Array.isArray(live?.listing_date?.corrections)||live.listing_date.corrections.length<1)errors.push("listing_correction");
      if(!Array.isArray(live?.issue_price?.corrections)||live.issue_price.corrections.length<1)errors.push("price_correction");
    }
    results.push({id,issuer_name:live?.issuer_name??null,listing_date:value(live,"listing_date"),errors});
  }

  const clean=data.records.filter(r=>r.id==="fabtech-technologies-cleanrooms-limited");
  if(clean.length!==1||clean[0].issuer_name!=="FABTECH TECHNOLOGIES CLEANROOMS LIMITED"||
     value(clean[0],"listing_date")!=="2025-01-10"||value(clean[0],"issue_price")!==85){
    results.push({id:"fabtech-technologies-cleanrooms-limited",issuer_name:clean[0]?.issuer_name??null,listing_date:value(clean[0],"listing_date"),errors:["cleanrooms_regression"]});
  }

  const proteanRaw=recovery["2023"]?.records?.find(r=>r.id==="protean-egov-technologies-limited");
  if(!proteanRaw?.secondary_listings?.some(x=>x.exchange==="NSE"&&x.listing_date==="2025-02-06"&&x.symbol==="PROTEAN")){
    results.push({id:"protean-secondary-listing",issuer_name:"Protean eGov Technologies Limited",listing_date:null,errors:["secondary_listing_not_retained"]});
  }

  return{
    schema_version:"1.0.0",status:results.every(r=>r.errors.length===0)?"verified":"failed",
    checked_at:checkedAt,dataset_generated_at:data.generated_at,published_records:data.records.length,
    checked_actions:5,failed_results:results.filter(r=>r.errors.length).length,
    receipt_artifact_id:receipt.workflow_artifact.artifact_id,results
  };
}
async function run(){
  const outputArg=process.argv.find(x=>x.startsWith("--output-dir="));
  if(!outputArg||process.argv.slice(2).some(x=>!x.startsWith("--output-dir=")))throw new Error("output_directory_required");
  const out=outputArg.slice("--output-dir=".length);fs.mkdirSync(out,{recursive:true});
  let report={status:"failed",source_url:LIVE_DATA_URL,run_id:process.env.GITHUB_RUN_ID||null,read_only:true};
  try{
    const reviewBytes=fs.readFileSync(path.join(ROOT,REVIEW_PATH));
    const review=JSON.parse(reviewBytes),receipt=JSON.parse(fs.readFileSync(path.join(ROOT,RECEIPT_PATH),"utf8"));
    const manifest=JSON.parse(fs.readFileSync(path.join(ROOT,MANIFEST_PATH),"utf8")),audit=JSON.parse(fs.readFileSync(path.join(ROOT,AUDIT_PATH),"utf8"));
    const bytes=await fetchPublishedSnapshot(),fetchedAt=new Date().toISOString();fs.writeFileSync(path.join(out,"deployed-data.json"),bytes);
    const result=auditBseReconciliationPublication({manifest,review,receipt,reviewBytes,audit,recovery:loadRecovery(ROOT),data:JSON.parse(bytes),checkedAt:new Date().toISOString()});
    report={...report,...result,manifest:MANIFEST_PATH,snapshot_fetched_at:fetchedAt,snapshot_sha256:hash(bytes),snapshot_bytes:bytes.length};
  }catch(e){report.error=e.message;}
  fs.writeFileSync(path.join(out,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));
  if(report.status!=="verified")process.exitCode=1;
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await run();
