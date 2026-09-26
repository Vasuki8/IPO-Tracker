import assert from "node:assert/strict";import {buildHistoricalRecord,isHistoricalEquityRow,isSupersededHistoricalObservation,materializeYear} from "./sync-nse-historical.mjs";
const rows=[{symbol:"ALPHA",company:"Alpha Limited",securityType:"EQ",listingDate:"15-JAN-2025",issuePrice:"125"},{symbol:"BETA",company:"Beta Limited",securityType:"SME",listingDate:"20-FEB-2025",issuePrice:"50"},{symbol:"OLD",company:"Old Limited",securityType:"EQ",listingDate:"20-DEC-2024",issuePrice:"10"},{symbol:"DEBT",company:"Debt Limited",securityType:"N1",listingDate:"01-MAR-2025",issuePrice:"1000"}];
assert.equal(isHistoricalEquityRow(rows[0],2025),true);assert.equal(isHistoricalEquityRow(rows[2],2025),false);assert.equal(isHistoricalEquityRow(rows[3],2025),false);
const rec=buildHistoricalRecord(rows[0],"2026-09-23T16:30:00Z");assert.equal(rec.board,"Mainboard");assert.equal(rec.listing_date.value,"2025-01-15");assert.equal(rec.issue_price.value,125);assert.equal(rec.status,"listed");
const manifest={records:[]};const result=materializeYear(rows,2025,manifest,"2026-09-23T16:30:00Z");assert.deepEqual(result,{official_rows:2,added:2,enriched:0,total_records:2});assert.equal(manifest.records[1].board,"SME");
const rerun=materializeYear(rows,2025,manifest,"2026-09-23T17:30:00Z");assert.equal(rerun.added,0);assert.equal(rerun.total_records,2);
console.log("NSE historical universe tests passed.");
// Multi-year invocation is covered by the same year-specific materializer; ensure
// adjacent historical years remain isolated.
const y2024={records:[]};const y2024Result=materializeYear(rows,2024,y2024,"2026-09-23T16:30:00Z");
assert.equal(y2024Result.official_rows,1);assert.equal(y2024.records[0].nse_symbol,"OLD");

const cams={symbol:"CAMS",company:"Computer Age Management Services Limited",securityType:"EQ",listingDate:"07-MAY-2021",issuePrice:"1240"};
const protean={symbol:"PROTEAN",company:"Protean eGov Technologies Limited",securityType:"EQ",listingDate:"06-FEB-2025",issuePrice:"1381"};
const superseded=[{symbol:"CAMS",listing_date:"2021-05-07"},{symbol:"PROTEAN",listing_date:"2025-02-06"}];
assert.equal(isSupersededHistoricalObservation(cams,superseded),true);
assert.equal(isSupersededHistoricalObservation(protean,superseded),true);
assert.equal(isSupersededHistoricalObservation(rows[0],superseded),false);
const suppressed={records:[]};const suppressedResult=materializeYear([...rows,cams,protean],2025,suppressed,"2026-09-26T18:40:00Z",superseded);
assert.equal(suppressedResult.official_rows,2);assert.equal(suppressed.records.some(r=>r.nse_symbol==="PROTEAN"),false);
