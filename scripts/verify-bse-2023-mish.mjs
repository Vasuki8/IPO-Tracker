import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {context,expected} from './apply-reviewed-bse-2023-mish.mjs';
import {LIVE_DATA_URL,fetchPublishedSnapshot} from './verify-bse-publication.mjs';

const sha256=b=>createHash('sha256').update(b).digest('hex');
const empty=()=>({value:null,status:'missing',evidence:[],corrections:[]});
const publicSource=s=>({
  url:s.url,
  document_type:s.document_type,
  document_identity:s.document_identity,
  publication_date:s.publication_date??null,
  page:s.page??null,
  collected_at:s.collected_at
});
const pubField=f=>f?.value==null
  ? {value:null,status:f?.status??'missing',evidence:[],corrections:f?.corrections??[]}
  : {value:f.value,status:f.status,evidence:[publicSource(f.source)],corrections:f.corrections??[]};

export const expectedPublic=r=>({
  id:r.id,
  issuer_name:r.issuer_name,
  board:r.board,
  board_evidence:(r.board_evidence||[]).map(publicSource),
  sector:r.sector,
  status:r.status,
  status_evidence:(r.status_evidence||[]).map(publicSource),
  price_band:pubField(r.price_band),
  issue_price:pubField(r.issue_price),
  issue_size_inr:pubField(r.issue_size_inr),
  market_lot:pubField(r.market_lot),
  minimum_bid_quantity:pubField(r.minimum_bid_quantity),
  minimum_application_amount_inr:empty(),
  application_requirements:{
    retail:{minimum_application_amount_inr:empty(),minimum_bid_quantity:empty()},
    non_institutional:{minimum_application_amount_inr:empty(),minimum_bid_quantity:empty()},
    anchor_investor:{minimum_application_amount_inr:empty(),minimum_bid_quantity:empty()}
  },
  open_date:pubField(r.open_date),
  close_date:pubField(r.close_date),
  listing_date:pubField(r.listing_date),
  documents:(r.documents||[]).map(x=>({
    type:x.type,
    identity:x.identity??null,
    url:x.url,
    publication_date:x.publication_date??null,
    collected_at:x.collected_at
  })),
  first_observed_at:r.first_observed_at,
  last_collected_at:r.last_collected_at
});

export async function verifyMishPublication({fetchImpl=fetch,outputDir=null,ctx=context()}={}){
  const target=expected(ctx).map(expectedPublic)[0];
  const bytes=await fetchPublishedSnapshot(fetchImpl),data=JSON.parse(bytes);
  if(outputDir){fs.mkdirSync(outputDir,{recursive:true});fs.writeFileSync(path.join(outputDir,'live-data.json'),bytes);}
  assert.equal(data?.schema_version,'1.2.0','invalid_published_dataset');
  assert.ok(Array.isArray(data.records),'invalid_published_records');
  const byId=new Map(data.records.map(r=>[r.id,r]));
  assert.equal(byId.size,data.records.length,'duplicate_published_id');
  assert.deepEqual(byId.get(target.id),target,'mish_public_projection_mismatch');
  const result={ok:true,url:LIVE_DATA_URL,checked_at:new Date().toISOString(),response_bytes:bytes.length,response_sha256:sha256(bytes),records:[target.id],generated_at:data.generated_at,published_records:data.records.length};
  if(outputDir)fs.writeFileSync(path.join(outputDir,'verification.json'),JSON.stringify(result,null,2)+'\n');
  return result;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  verifyMishPublication({outputDir:process.env.VERIFICATION_DIR||null})
    .then(x=>console.log(JSON.stringify({mish_live_verification:x})))
    .catch(e=>{console.error(e.stack||e.message);process.exitCode=1;});
}
