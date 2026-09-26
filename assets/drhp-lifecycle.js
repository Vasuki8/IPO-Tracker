/* Shared draft-filing to IPO-lifecycle reconciliation for browser UI and Node tests. */
export const NORMAL_IPO_LIFECYCLE_STATUSES=Object.freeze(["upcoming","open","closed","listed"]);
const NORMAL_STATUS_SET=new Set(NORMAL_IPO_LIFECYCLE_STATUSES);
export function canonicalLifecycleIssuer(value){
  return String(value??"").replace(/\s+/g," ").trim().toLowerCase().replace(/&/g," and ")
    .replace(/\bltd\.?\b/g," limited ").replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
}
function cleanId(v){const x=String(v??"").trim().toUpperCase();return x&&x!=="-"?x:null;}
function identityNames(record){
  const names=[record?.issuer_name];for(const key of ["issuer_aliases","aliases","previous_names"])if(Array.isArray(record?.[key]))names.push(...record[key].filter(v=>typeof v==="string"));
  return [...new Set(names.map(canonicalLifecycleIssuer).filter(Boolean))];
}
function addIndex(index,key,record){
  if(!key)return;const list=index.get(key)||[];
  if(!list.some(x=>x.id===record.id&&x.status===record.status))list.push(record);
  index.set(key,list);
}
export function buildIpoLifecycleIndex(ipoData){
  if(!ipoData||!Array.isArray(ipoData.records))throw new Error("invalid_ipo_dataset");
  const index=new Map();
  for(const source of ipoData.records){
    const status=String(source?.status??"").toLowerCase();if(!NORMAL_STATUS_SET.has(status))continue;
    const record={id:source.id??null,issuer_name:source.issuer_name,status,board:source.board??null,nse_symbol:source.nse_symbol??null,isin:source.isin??null};
    for(const name of identityNames(source))addIndex(index,"name:"+name,record);
    addIndex(index,"isin:"+cleanId(source.isin),record);addIndex(index,"symbol:"+cleanId(source.nse_symbol),record);
  }
  return index;
}
function normalizedFiling(f,authority){
  const type=String(f?.filing_type||"DRHP").trim().toUpperCase(),date=String(f?.filing_date||"").trim(),url=String(f?.filing_url||"").trim();
  if(!date||!url)return null;
  return {...f,filing_type:type,filing_date:date,filing_url:url,source_authority:authority,
    source_evidence_list:Array.isArray(f?.source_evidence_list)?f.source_evidence_list:(f?.source_evidence?[f.source_evidence]:[])};
}
function preferFiling(a,b){
  const rank=f=>f.source_authority==="SEBI"?0:1;
  return rank(a)<=rank(b)?a:b;
}
export function mergeOfficialDraftSources(sebiData,nseData){
  if(!sebiData||!Array.isArray(sebiData.companies))throw new Error("invalid_sebi_drhp_dataset");
  if(!nseData||!Array.isArray(nseData.companies))throw new Error("invalid_nse_drhp_dataset");
  const groups=new Map();
  function absorb(company,authority){
    const key=canonicalLifecycleIssuer(company?.issuer_name);if(!key)throw new Error("invalid_draft_issuer");
    const g=groups.get(key)||{issuer_name:company.issuer_name,events:new Map(),board_hints:new Set(),isins:new Set(),symbols:new Set(),processing_statuses:new Set()};
    for(const board of company.board_hints||[])if(board)g.board_hints.add(board);
    for(const isin of company.isins||[])if(cleanId(isin))g.isins.add(cleanId(isin));
    for(const symbol of company.symbols||[])if(cleanId(symbol))g.symbols.add(cleanId(symbol));
    if(company.latest_processing_status)g.processing_statuses.add(company.latest_processing_status);
    for(const raw of company.filings||[]){
      const f=normalizedFiling(raw,authority);if(!f)continue;
      if(raw.isin&&cleanId(raw.isin))g.isins.add(cleanId(raw.isin));if(raw.symbol&&cleanId(raw.symbol))g.symbols.add(cleanId(raw.symbol));if(raw.board)g.board_hints.add(raw.board);
      if(raw.processing_status)g.processing_statuses.add(raw.processing_status);
      const eventKey=f.filing_date+"|"+f.filing_type;
      const old=g.events.get(eventKey);
      if(!old)g.events.set(eventKey,{...f,source_evidence_list:[...f.source_evidence_list],alternate_official_urls:[]});
      else{
        const preferred=preferFiling(old,f),other=preferred===old?f:old;
        const merged={...preferred,source_evidence_list:[...(preferred.source_evidence_list||[]),...(other.source_evidence_list||[])],
          alternate_official_urls:[...new Set([...(preferred.alternate_official_urls||[]),...(other.alternate_official_urls||[]),other.filing_url].filter(u=>u&&u!==preferred.filing_url))]};
        if(!merged.processing_status&&other.processing_status)merged.processing_status=other.processing_status;
        if(!merged.issue_open_date&&other.issue_open_date)merged.issue_open_date=other.issue_open_date;
        if(!merged.issue_close_date&&other.issue_close_date)merged.issue_close_date=other.issue_close_date;
        g.events.set(eventKey,merged);
      }
    }
    groups.set(key,g);
  }
  for(const c of sebiData.companies)absorb(c,"SEBI");for(const c of nseData.companies)absorb(c,"NSE");
  return {schema_version:"1.0.0",companies:[...groups.values()].map(g=>{
    const filings=[...g.events.values()].sort((a,b)=>b.filing_date.localeCompare(a.filing_date)||a.filing_type.localeCompare(b.filing_type));
    const latest=filings[0];return {issuer_name:g.issuer_name,latest_filing_date:latest.filing_date,latest_filing_type:latest.filing_type,latest_filing_url:latest.filing_url,
      latest_processing_status:[...g.processing_statuses].at(-1)||null,board_hints:[...g.board_hints].sort(),isins:[...g.isins].sort(),symbols:[...g.symbols].sort(),
      filing_count:filings.length,filings,source_authorities:[...new Set(filings.map(f=>f.source_authority))].sort()};
  }).sort((a,b)=>b.latest_filing_date.localeCompare(a.latest_filing_date)||a.issuer_name.localeCompare(b.issuer_name))};
}
function matchLifecycle(index,company){
  const keys=["name:"+canonicalLifecycleIssuer(company.issuer_name),...(company.isins||[]).map(x=>"isin:"+cleanId(x)),...(company.symbols||[]).map(x=>"symbol:"+cleanId(x))];
  const seen=new Map();for(const key of keys)for(const match of index.get(key)||[])seen.set((match.id||"")+"|"+match.status,match);
  return [...seen.values()];
}
function hasOfficialIssueDate(company){return (company.filings||[]).some(f=>Boolean(f.issue_open_date||f.issue_close_date));}
export function buildPreIpoView(draftData,ipoData){
  if(!draftData||!Array.isArray(draftData.companies))throw new Error("invalid_draft_dataset");
  const index=buildIpoLifecycleIndex(ipoData),companies=[],transitioned=[],lifecycle_gaps=[];
  for(const sourceCompany of draftData.companies){
    const matches=matchLifecycle(index,sourceCompany),dateSignal=hasOfficialIssueDate(sourceCompany);
    if(matches.length||dateSignal){
      const item={issuer_name:sourceCompany.issuer_name,latest_filing_date:sourceCompany.latest_filing_date,matches,official_issue_date_signal:dateSignal};
      transitioned.push(item);if(dateSignal&&!matches.length)lifecycle_gaps.push(item);continue;
    }
    companies.push({...sourceCompany,lifecycle_stage:"drhp_filed_pre_ipo"});
  }
  return {companies,transitioned,lifecycle_gaps,counts:{source_companies:draftData.companies.length,pre_ipo_companies:companies.length,
    transitioned_companies:transitioned.length,lifecycle_gaps:lifecycle_gaps.length,source_filings:draftData.companies.reduce((s,c)=>s+(c.filings?.length||0),0),
    pre_ipo_filings:companies.reduce((s,c)=>s+(c.filings?.length||0),0)},lifecycle_statuses:NORMAL_IPO_LIFECYCLE_STATUSES};
}
