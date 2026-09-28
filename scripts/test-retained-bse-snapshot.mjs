import assert from 'node:assert/strict';
import fs from 'node:fs';
import {SUMMARY,QUEUE,validateSnapshot} from './check-retained-bse-snapshot.mjs';
const original=[fs.readFileSync(SUMMARY),fs.readFileSync(QUEUE)],s=JSON.parse(original[0]),q=JSON.parse(original[1]);
const before=structuredClone([s,q]);assert.equal(validateSnapshot(s,q).ok,true);assert.deepEqual([s,q],before);
let rejected=0;
for(const edit of [
 (s,q)=>s.auto_import_allowed=true,(s,q)=>s.source_refetched=true,(s,q)=>s.full_indian_ipo_universe_complete=true,
 (s,q)=>s.years[0].exact++,(s,q)=>s.totals.awaiting_review++,(s,q)=>s.reconciled_at='2020-01-01',
 (s,q)=>s.source_pin.source_commit_labels_disagree=false,(s,q)=>s.exceptions.source_commit_labels_disagree=false,
 (s,q)=>s.source_pin.receipts[0].file='../escape',(s,q)=>s.source_pin.total_response_bytes++,
 (s,q)=>s.full_report.sha256='bad',(s,q)=>s.alias_approvals.pop(),(s,q)=>s.recovery_snapshot.commit='main',
 (s,q)=>q.auto_import_allowed=true,(s,q)=>q.rows.pop(),(s,q)=>q.rows[0].matched_id='invented',
 (s,q)=>q.rows[0].disposition='published_reviewed_ipo',(s,q)=>q.rows[1].bse_scrip_code=q.rows[0].bse_scrip_code,
 (s,q)=>q.rows[1].source_row_index=q.rows[0].source_row_index,(s,q)=>q.reconciliation_full_sha256='0'.repeat(64),
 (s,q)=>q.next_bounded_review_codes=['999999'],(s,q)=>q.next_bounded_review_codes=[],(s,q)=>q.source_collected_at=s.reconciled_at
]){const b=structuredClone([s,q]);edit(...b);assert.throws(()=>validateSnapshot(...b));rejected++;}
assert.throws(()=>validateSnapshot(s,q,Buffer.from('{}')));rejected++;
assert.deepEqual(fs.readFileSync(SUMMARY),original[0]);assert.deepEqual(fs.readFileSync(QUEUE),original[1]);
console.log(JSON.stringify({retained_snapshot_tests:{rejected_cases:rejected,source_clock:true,queue_binding:true,discovery_only:true,read_only:true}}));
