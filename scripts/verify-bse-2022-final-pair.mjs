import fs from "node:fs";
import {sha256} from "./verify-bse-listing-candidates.mjs";
import assert from "node:assert/strict";
import path from "node:path";
import {pathToFileURL} from "node:url";
import {context,expected} from "./apply-reviewed-bse-2022-final-pair.mjs";
import {LIVE_DATA_URL,fetchPublishedSnapshot} from "./verify-bse-publication.mjs";

const empty=()=>({value:null,status:"missing",evidence:[],corrections:[]});
const publicSource=s=>({url:s.url,document_type:s.document_type,document_identity:s.document_identity,publication_date:s.publication_date??null,page:s.page??null,collected_at:s.collected_at});
const pubField=f=>f?.value==null?empty():({value:f.value,status:f.status,evidence:[{...f.source,page:f.page??null},...(f.additional_sources??[])].map(publicSource),corrections:f.corrections||[]});
export const expectedPublic=r=>({
 id:r.id,issuer_name:r.issuer_name,board:r.board,board_evidence:(r.board_evidence||[]).map(publicSource),sector:r.sector,status:r.status,status_evidence:(r.status_evidence||[]).map(publicSource),
 price_band:pubField(r.price_band),issue_price:pubField(r.issue_price),issue_size_inr:pubField(r.issue_size_inr),market_lot:pubField(r.market_lot),minimum_bid_quantity:pubField(r.minimum_bid_quantity),minimum_application_amount_inr:empty(),
 application_requirements:{retail:{minimum_application_amount_inr:empty(),minimum_bid_quantity:empty()},non_institutional:{minimum_application_amount_inr:empty(),minimum_bid_quantity:empty()},anchor_investor:{minimum_application_amount_inr:empty(),minimum_bid_quantity:empty()}},
 open_date:pubField(r.open_date),close_date:pubField(r.close_date),listing_date:pubField(r.listing_date),
 documents:(r.documents||[]).map(x=>({type:x.type,identity:x.identity??null,url:x.url,publication_date:x.publication_date??null,collected_at:x.collected_at})),
 first_observed_at:r.first_observed_at,last_collected_at:r.last_collected_at
});
export async function verifyFinalPairPublication({fetchImpl=fetch,outputDir=null}={}){
 const targets=expected(context()).map(expectedPublic);
 const bytes=await fetchPublishedSnapshot(fetchImpl),snap=JSON.parse(bytes);
 if(outputDir){fs.mkdirSync(outputDir,{recursive:true});fs.writeFileSync(path.join(outputDir,"live-data.json"),bytes);}
 assert.equal(snap?.schema_version,"1.2.0","invalid_published_dataset");
 assert.ok(Array.isArray(snap.records),"invalid_published_records");
 const byId=new Map(snap.records.map(r=>[r.id,r]));
 assert.equal(byId.size,snap.records.length,"duplicate_published_id");
 for(const target of targets){
   assert.ok(byId.has(target.id),`published_record_missing:${target.id}`);
   assert.deepEqual(byId.get(target.id),target,`published_record_mismatch:${target.id}`);
 }
 return{ok:true,url:LIVE_DATA_URL,checked_at:new Date().toISOString(),response_bytes:bytes.length,response_sha256:sha256(bytes),records:targets.map(x=>x.id),generated_at:snap.generated_at,published_records:snap.records.length,verified_new_fields:8,filled_existing_fields:4,existing_conflicts:1};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 verifyFinalPairPublication({outputDir:process.env.VERIFICATION_DIR||null})
   .then(x=>{if(process.env.VERIFICATION_DIR)fs.writeFileSync(path.join(process.env.VERIFICATION_DIR,"verification.json"),JSON.stringify(x,null,2)+"\n");console.log(JSON.stringify({bse_2022_final_pair_live_verification:x}));})
   .catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
}
