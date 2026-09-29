import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const req=(ok,message)=>{if(!ok)throw new Error(message);};
const sha256=b=>createHash('sha256').update(b).digest('hex');
const compact=s=>s.replace(/\s+/g,' ').trim();
const clip=(s,index)=>compact(s.slice(Math.max(0,index-350),Math.min(s.length,index+1050))).slice(0,1400);
function pageCount(info){const m=String(info).match(/^Pages:\s+(\d+)\s*$/mi);return m?Number(m[1]):null;}
export function buildExtractionIndex(dir){
 const receipt=JSON.parse(fs.readFileSync(path.join(dir,'source-receipt.json'),'utf8'));
 req(receipt.status==='complete'&&receipt.publication_import_allowed===false&&receipt.semantic_review_complete===false,'unsafe_or_incomplete_receipt');
 const documents=[];
 for(const d of receipt.documents){
  req(d.accepted&&/^[a-f0-9]{64}$/.test(d.response_sha256)&&d.response_bytes>0&&/^\d{6}-annual-2023-24\.pdf$/.test(d.evidence_file),'invalid_retained_document');
  const pdf=fs.readFileSync(path.join(dir,d.evidence_file));
  req(pdf.length===d.response_bytes&&sha256(pdf)===d.response_sha256&&pdf.subarray(0,5).toString('ascii')==='%PDF-','retained_pdf_mismatch');
  const base=path.join(dir,d.evidence_file.slice(0,-4));
  const text=fs.readFileSync(base+'.txt','utf8'),info=fs.readFileSync(base+'.pdfinfo','utf8');
  const pages=text.split('\f'),reported=pageCount(info);
  req(Number.isSafeInteger(reported)&&reported>0,'missing_pdf_page_count');
  const listing_hits=[],code_hits=[];
  for(let n=0;n<pages.length;n++){
   const page=pages[n],normalized=compact(page);
   if(!normalized)continue;
   const listingMatch=normalized.match(/\b(?:listed|listing|trading)\b/i);
   if(listingMatch&&/\b(?:BSE|Bombay Stock Exchange|SME)\b/i.test(normalized)&&listing_hits.length<16)listing_hits.push({physical_page:n+1,snippet:clip(normalized,listingMatch.index)});
   const codeIndex=normalized.indexOf(d.code);
   if(codeIndex>=0&&code_hits.length<10)code_hits.push({physical_page:n+1,snippet:clip(normalized,codeIndex)});
  }
  documents.push({code:d.code,issuer_name:d.issuer_name,evidence_file:d.evidence_file,response_sha256:d.response_sha256,response_bytes:d.response_bytes,pdf_pages:reported,listing_hits,code_hits});
 }
 return{schema_version:'1.0.0',status:'extraction_research_only',batch_id:receipt.batch_id,semantic_review_complete:false,publication_import_allowed:false,documents};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 try{
  const args=process.argv.slice(2);req(args.length===1&&args[0].startsWith('--dir='),'use --dir=ABSOLUTE_EVIDENCE_DIRECTORY');
  const dir=args[0].slice(6);req(path.isAbsolute(dir),'absolute_evidence_directory_required');
  const index=buildExtractionIndex(dir);
  fs.writeFileSync(path.join(dir,'extraction-index.json'),JSON.stringify(index,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(index,null,2));
 }catch(e){console.error(e.message);process.exitCode=1;}
}
