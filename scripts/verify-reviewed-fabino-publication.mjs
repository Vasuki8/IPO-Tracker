import fs from "node:fs";
import path from "node:path";
import {fileURLToPath,pathToFileURL} from "node:url";
import {MANIFEST_PATH,RECEIPT_PATH,REVIEW_PATH,applyReviewedFabino,fabinoRecoveryRecord,loadRecovery} from "./apply-reviewed-fabino.mjs";
import {fetchPublishedSnapshot,LIVE_DATA_URL} from "./verify-bse-publication.mjs";
import {hash} from "./apply-reviewed-nse-ipos.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const issuerKey=value=>String(value??"").toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ").replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const sourceMatch=(actual,expected)=>["url","document_type","document_identity","publication_date","page","collected_at"].every(k=>actual?.[k]===expected?.[k]);

export function auditFabinoPublication({manifest,review,receipt,reviewBytes,recovery,data,checkedAt}){
  if(data?.schema_version!=="1.2.0"||!Array.isArray(data.records)||!Number.isFinite(Date.parse(checkedAt)))throw new Error("invalid_public_snapshot");
  const plan=applyReviewedFabino(recovery,data,manifest,review,receipt,reviewBytes);
  if(plan.stats.added!==0)throw new Error("reviewed_fabino_not_in_recovery");
  const expected=fabinoRecoveryRecord(manifest,review,receipt,reviewBytes);
  const raw=(recovery["2022"]?.records||[]).find(r=>r.id===expected.id);
  const hits=data.records.filter(r=>r.id===expected.id||issuerKey(r.issuer_name)===issuerKey(expected.issuer_name));
  const live=hits.length===1?hits[0]:null;
  const errors=[];
  if(!raw||!live||live.id!==expected.id||issuerKey(live.issuer_name)!==issuerKey(expected.issuer_name)||live.board!=="SME"||live.status!=="listed")errors.push("identity_board_status");
  if(raw?.bse_scrip_code!=="543444"||raw?.isin!=="INE0DRT01018"||raw?.fabino_listing_year_correction?.manifest!==MANIFEST_PATH)errors.push("retained_identity_or_review");
  if(!raw?.listing_date?.corrections?.some(c=>c.previous_value==="2021-01-13"&&c.replacement_value==="2022-01-13"))errors.push("retained_listing_year_correction");

  for(const fieldName of Object.keys(manifest.fields)){
    const expectedField=expected[fieldName];
    if(!same(live?.[fieldName]?.value,expectedField?.value)||live?.[fieldName]?.status!=="verified"||
       !live?.[fieldName]?.evidence?.some(src=>sourceMatch(src,expectedField.source)))errors.push(fieldName);
    if(raw?.[fieldName]?.source?.document_sha256!==expectedField?.source?.document_sha256)errors.push(fieldName+"_hash");
  }
  if(!same(live?.listing_date?.corrections,expected.listing_date.corrections))errors.push("public_listing_year_correction");
  if(live?.minimum_application_amount_inr?.value!==null)errors.push("out_of_scope_application_amount");
  return{
    schema_version:"1.0.0",
    status:errors.length?"failed":"verified",
    checked_at:checkedAt,
    dataset_generated_at:data.generated_at,
    published_records:data.records.length,
    receipt_artifact_id:receipt.workflow_artifact.artifact_id,
    issuer_name:expected.issuer_name,
    listing_date:live?.listing_date?.value??null,
    checked_fields:Object.keys(manifest.fields).length,
    errors
  };
}

async function run(){
  const outputArg=process.argv.find(arg=>arg.startsWith("--output-dir="));
  if(!outputArg||process.argv.slice(2).some(arg=>!arg.startsWith("--output-dir=")))throw new Error("output_directory_required");
  const output=outputArg.slice("--output-dir=".length);
  fs.mkdirSync(output,{recursive:true});
  let report={status:"failed",source_url:LIVE_DATA_URL,run_id:process.env.GITHUB_RUN_ID||null,read_only:true};
  try{
    const reviewBytes=fs.readFileSync(path.join(ROOT,REVIEW_PATH));
    const review=JSON.parse(reviewBytes);
    const receipt=JSON.parse(fs.readFileSync(path.join(ROOT,RECEIPT_PATH),"utf8"));
    const manifest=JSON.parse(fs.readFileSync(path.join(ROOT,MANIFEST_PATH),"utf8"));
    const bytes=await fetchPublishedSnapshot(),fetchedAt=new Date().toISOString();
    fs.writeFileSync(path.join(output,"deployed-data.json"),bytes);
    const audit=auditFabinoPublication({manifest,review,receipt,reviewBytes,recovery:loadRecovery(ROOT),data:JSON.parse(bytes),checkedAt:new Date().toISOString()});
    report={...report,...audit,manifest:MANIFEST_PATH,snapshot_fetched_at:fetchedAt,snapshot_sha256:hash(bytes),snapshot_bytes:bytes.length};
  }catch(error){report.error=error.message;}
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify(report));
  if(report.status!=="verified")process.exitCode=1;
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await run();
