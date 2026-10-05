// Deterministic UI-only examples. Never imported by collectors or publication.
// These synthetic values test behavior; they are not investment data.
const collected = "2026-09-25T12:00:00Z";
const evidence = {url:"https://www.sebi.gov.in/", document_type:"SEBI Prospectus fixture",
  document_identity:"Synthetic browser fixture", publication_date:"2026-09-24", page:1, collected_at:collected};
export const verified = value => ({value, status:"verified", evidence:[{...evidence}], corrections:[]});
export const missing = () => ({value:null, status:"missing", evidence:[], corrections:[]});
export function ipo(id, overrides = {}) {
  const requirement = () => ({minimum_application_amount_inr:missing(), minimum_bid_quantity:missing()});
  return {id, issuer_name:id, board:"SME", board_evidence:[{...evidence}], sector:null,
    status:"listed", status_evidence:[{...evidence}], price_band:verified({min:100,max:110}),
    issue_price:verified(110), issue_size_inr:verified(50000000), market_lot:verified(100),
    minimum_bid_quantity:verified(200), minimum_application_amount_inr:missing(),
    application_requirements:{retail:requirement(),non_institutional:requirement(),anchor_investor:requirement()},
    open_date:verified("2026-09-01"),close_date:verified("2026-09-03"),listing_date:verified("2026-09-08"),
    documents:[{type:"SEBI Prospectus fixture",identity:"Synthetic offer document",url:"https://www.sebi.gov.in/",
      publication_date:"2026-09-24",collected_at:collected},
      {type:"NSE Exchange fixture",identity:"Synthetic exchange record",url:"https://www.nseindia.com/",
      publication_date:"2026-09-24",collected_at:collected}],
    first_observed_at:collected,last_collected_at:collected,...overrides};
}
export function productDataset() {
  const open = (id, closing) => ipo(id, {issuer_name:id,status:"open",open_date:verified("2026-09-28"),
    close_date:verified(closing),listing_date:missing()});
  return {schema_version:"1.2.0",generated_at:"2026-09-30T11:00:00Z", records:[
    open("Fixture Closes Today A", "2026-09-30"), open("Fixture Closes Today B", "2026-09-30"),
    ...["A","B","C","D"].map(s => open("Fixture Still Open " + s, "2026-10-05")),
    ipo("fixture-expired", {issuer_name:"Fixture Expired Limited",status:"open",
      open_date:verified("2026-09-18"),close_date:verified("2026-09-22"),listing_date:missing()}),
    ipo("fixture-expired-b", {issuer_name:"Fixture Expired B",status:"open",close_date:verified("2026-09-23"),listing_date:missing()}),
    ipo("fixture-expired-c", {issuer_name:"Fixture Expired C",status:"open",close_date:verified("2026-09-24"),listing_date:missing()}),
    ipo("fixture-price-conflict", {issuer_name:"Fixture Price Conflict Limited",price_band:verified({min:131,max:138}),
      issue_price:verified(60),market_lot:missing(),minimum_bid_quantity:verified(1000)}),
    ipo("fixture-trading-lot", {issuer_name:"Fixture Trading Lot Limited",market_lot:verified(1),minimum_bid_quantity:verified(150)}),
    ipo("fixture-bank", {issuer_name:"Fixture Bank Limited",board:"Mainboard"}),
    ipo("fixture-unknown-board", {issuer_name:"Fixture Unknown Board Limited",board:null,board_evidence:[]}),
  ]};
}
export function directoryDataset() {
  // 101 records exercise all three page sizes and multiple pages without corpus assumptions.
  return {schema_version:"1.2.0",generated_at:"2026-09-30T11:00:00Z", records:Array.from({length:101}, (_,i) =>
    ipo("fixture-directory-" + String(i).padStart(3,"0"), {
      issuer_name:"Fixture Company " + String(i).padStart(3,"0") + " Limited",
      board:i%2?"SME":"Mainboard",
      ...(i<2?{status:"open",open_date:verified("2026-09-28"),close_date:verified("2026-10-05"),listing_date:missing()}:{})}))};
}
export function draftDataset() {
  const filing = {filing_type:"DRHP",filing_date:"2026-09-22",
    filing_url:"https://www.sebi.gov.in/filings/public-issues/sep-2026/synthetic-fixture.html"};
  return {schema_version:"1.0.0",generated_at:"2026-09-28T14:00:00Z",collection_completed_at:"2026-09-28T13:00:00Z",
    coverage:{year:2026,companies:1,filing_records:1,pages_fetched:2,stop_reason:"first_page_strictly_older_than_year"},
    source_pages:[{observed_records:1},{observed_records:1}],
    companies:[{issuer_name:"Fixture Draft Limited",filing_count:1,filings:[filing],latest_filing_type:filing.filing_type,
      latest_filing_date:filing.filing_date,latest_filing_url:filing.filing_url}]};
}
export const failedDraftHealth = () => ({schema_version:"1.0.0",status:"failed",attempted_at:"2026-09-30T12:00:00Z",
  last_successful_collection_at:"2026-09-28T13:00:00Z"});
