const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
function runtime() {
  const panel = {hidden:true, innerHTML:'', querySelector:()=>null};
  const context = {renderSourceHealth:()=>{}, state:{meta:{generatedAt:'2026-09-18T08:00:00Z',sourceHealth:{}}},
    els:{health:{querySelectorAll:()=>[]}}, document:{addEventListener:()=>{}, getElementById:()=>panel},
    setTimeout:()=>{}, formatTimestamp:value=>value, escapeHtml:value=>String(value), escapeAttr:value=>String(value)};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(root,'source-health.js'),'utf8'), context);
  return {context,panel};
}
const fixtures = JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/operational_health.json'),'utf8'));
for (const fixture of fixtures) test('recorded source semantics: '+fixture.name,()=>{
  const {context}=runtime();
  context.input=fixture.health;
  assert.equal(vm.runInContext('recordedSourceOutcome(input)',context),fixture.outcome);
  assert.equal(vm.runInContext('sourceCheckClock(input).state',context),fixture.clock);
});
test('public diagnostics never borrow dataset generation time for a missing check',()=>{
  const {context,panel}=runtime();
  context.state.meta.sourceHealth['NSE-live']={ok:true,records:12};
  vm.runInContext("openHealthDetail('NSE-live')",context);
  assert.match(panel.innerHTML,/Last source check<\/div><div class="health-detail-value">Not available/);
  assert.doesNotMatch(panel.innerHTML,/2026-09-18T08:00:00Z/);
  assert.match(panel.innerHTML,/Collection reported/);
  assert.match(panel.innerHTML,/does not establish a fresh source observation/);
});
test('public diagnostics expose deferred work and conflicting check clocks',()=>{
  const {context,panel}=runtime();
  context.state.meta.sourceHealth.BSE={ok:true,status:'deferred',checkedAt:'2026-09-18T08:00:00Z',asOf:'2026-09-18T07:00:00Z'};
  vm.runInContext("openHealthDetail('BSE')",context);
  assert.match(panel.innerHTML,/Deferred/);
  assert.match(panel.innerHTML,/Conflicting check timestamps/);
  assert.doesNotMatch(panel.innerHTML,/Healthy/);
});

test('unbound legacy diagnostics remain visible without replacing a recorded outcome',()=>{
  const {context,panel}=runtime();
  context.state.meta.errors=['BSE public issues: earlier fallback failed'];
  context.state.meta.sourceHealth.BSE={ok:true,records:8};
  vm.runInContext("openHealthDetail('BSE')",context);
  assert.match(panel.innerHTML,/Collection reported/);
  assert.match(panel.innerHTML,/Retained diagnostic/);
  assert.match(panel.innerHTML,/earlier fallback failed/);
});
