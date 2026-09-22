const IPO_DATA = [
  {id:"aarav-mobility",initials:"AM",company:"Aarav Mobility Limited",sector:"Auto Components",board:"Mainboard",status:"open",price:"₹520 – ₹548",lot:27,minimum:"₹14,796",dates:"20–23 Sep",issue:"₹900 Cr",sourceStatus:"verified",source:"Price Band Advertisement",sourceDate:"18 Sep 2026"},
  {id:"nova-energy",initials:"NE",company:"Nova Energy Systems",sector:"Industrial Equipment",board:"Mainboard",status:"open",price:"₹310 – ₹326",lot:45,minimum:"₹14,670",dates:"21–24 Sep",issue:"₹640 Cr",sourceStatus:"provisional",source:"Exchange Notice",sourceDate:"19 Sep 2026"},
  {id:"verdant-foods",initials:"VF",company:"Verdant Foods Limited",sector:"Consumer Foods",board:"Mainboard",status:"upcoming",price:"₹210 – ₹225",lot:65,minimum:"₹14,625",dates:"25–29 Sep",issue:"₹480 Cr",sourceStatus:"verified",source:"Price Band Advertisement",sourceDate:"20 Sep 2026"},
  {id:"orbit-tech",initials:"OT",company:"Orbit Tech Solutions",sector:"IT Services",board:"SME",status:"upcoming",price:"₹138 – ₹145",lot:1000,minimum:"₹1,45,000",dates:"28–30 Sep",issue:"₹72 Cr",sourceStatus:"missing",source:"Source not retained",sourceDate:"—"},
  {id:"blueforge",initials:"BF",company:"BlueForge Engineering",sector:"Capital Goods",board:"SME",status:"closed",price:"₹96 – ₹102",lot:1200,minimum:"₹1,22,400",dates:"16–18 Sep",issue:"₹54 Cr",sourceStatus:"verified",source:"RHP / Price Notice",sourceDate:"14 Sep 2026"},
  {id:"zenith-care",initials:"ZC",company:"Zenith Care Limited",sector:"Healthcare",board:"Mainboard",status:"listed",price:"₹145",lot:100,minimum:"₹14,500",dates:"10–12 Sep",issue:"₹310 Cr",sourceStatus:"verified",source:"Final Prospectus",sourceDate:"15 Sep 2026"}
];

const state = { board:"all", status:"all", query:"" };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function statusBadge(status){
  const label = {open:"OPEN",upcoming:"UPCOMING",closed:"CLOSED",listed:"LISTED"}[status] || status.toUpperCase();
  return `<span class="status status--${status}">${label}</span>`;
}
function sourceBadge(sourceStatus){
  const labels = {verified:"✓ VERIFIED",provisional:"PROVISIONAL",missing:"SOURCE MISSING"};
  return `<span class="source source--${sourceStatus}">${labels[sourceStatus]}</span>`;
}
function filteredRows(){
  return IPO_DATA.filter((ipo) => {
    const boardMatch = state.board === "all" || ipo.board.toLowerCase() === state.board;
    const statusMatch = state.status === "all" || ipo.status === state.status;
    const haystack = [ipo.company, ipo.sector, ipo.board].join(" ").toLowerCase();
    const queryMatch = !state.query || haystack.includes(state.query);
    return boardMatch && statusMatch && queryMatch;
  });
}
function render(){
  const rows = filteredRows();
  $("#ipoRows").innerHTML = rows.map((ipo) => `
    <tr>
      <td class="company-cell"><div class="company-row"><div class="company-logo">${ipo.initials}</div><div><div class="company-name">${ipo.company}</div><div class="company-meta">${ipo.board} · ${ipo.sector}</div></div></div></td>
      <td>${statusBadge(ipo.status)}</td>
      <td><div class="number">${ipo.price}</div><div class="secondary">Price band</div></td>
      <td><div class="number">${ipo.lot.toLocaleString("en-IN")} shares</div><div class="secondary">${ipo.minimum} minimum</div></td>
      <td><div class="number">${ipo.dates}</div><div class="secondary">2026</div></td>
      <td><div class="number">${ipo.issue}</div></td>
      <td>${sourceBadge(ipo.sourceStatus)}<div class="secondary source-stack">${ipo.source}</div></td>
      <td><button class="view-button" data-ipo="${ipo.id}">View →</button></td>
    </tr>`).join("");

  $("#mobileCards").innerHTML = rows.map((ipo) => `
    <article class="mobile-card">
      <div class="mobile-card__head"><div><div class="company-name">${ipo.company}</div><div class="company-meta">${ipo.board} · ${ipo.sector}</div></div>${statusBadge(ipo.status)}</div>
      <div class="mobile-price">${ipo.price}</div>
      <div class="mobile-grid">
        <div><div class="kv-label">LOT SIZE</div><div class="kv-value">${ipo.lot.toLocaleString("en-IN")} shares</div></div>
        <div><div class="kv-label">MINIMUM</div><div class="kv-value">${ipo.minimum}</div></div>
        <div><div class="kv-label">DATES</div><div class="kv-value">${ipo.dates}</div></div>
        <div><div class="kv-label">ISSUE SIZE</div><div class="kv-value">${ipo.issue}</div></div>
      </div>
      <div class="mobile-card__foot">${sourceBadge(ipo.sourceStatus)}<button class="view-button" data-ipo="${ipo.id}">View IPO →</button></div>
    </article>`).join("");

  $("#emptyState").hidden = rows.length !== 0;
  $("#metricOpen").textContent = IPO_DATA.filter((x) => x.status === "open").length;
  $("#metricUpcoming").textContent = IPO_DATA.filter((x) => x.status === "upcoming").length;
  $("#metricListed").textContent = IPO_DATA.filter((x) => x.status === "listed").length;
  bindDynamicButtons();
}
function bindDynamicButtons(){
  $$("[data-ipo]").forEach((button) => button.addEventListener("click", () => showDetail(button.dataset.ipo)));
}
function setActive(group, active){
  group.forEach((button) => button.classList.toggle("active", button === active));
}
function syncSearch(value){
  state.query = value.trim().toLowerCase();
  $("#topSearch").value = value;
  $("#heroSearch").value = value;
  render();
}
function showHome(){
  $("#homeView").hidden = false;
  $("#detailView").hidden = true;
  window.scrollTo({top:0,behavior:"smooth"});
  history.replaceState(null,"","#");
}
function showDetail(id){
  const ipo = IPO_DATA.find((row) => row.id === id) || IPO_DATA[0];
  $("#detailLogo").textContent = ipo.initials;
  $("#detailName").textContent = ipo.company;
  $("#detailBoard").textContent = ipo.board;
  $("#detailSector").textContent = ipo.sector;
  $("#detailStatus").className = `status status--${ipo.status}`;
  $("#detailStatus").textContent = ipo.status.toUpperCase();
  ["#detailPrice","#detailPrice2","#sidePrice"].forEach((id) => $(id).textContent = ipo.price);
  ["#detailIssue","#detailIssue2"].forEach((id) => $(id).textContent = ipo.issue);
  ["#detailLot","#detailLot2","#detailBid"].forEach((id) => $(id).textContent = `${ipo.lot.toLocaleString("en-IN")} shares`);
  ["#detailMinimum","#detailMinimum2"].forEach((id) => $(id).textContent = ipo.minimum);
  $("#detailSource").textContent = ipo.source;
  $("#detailSourceDate").textContent = ipo.sourceDate;
  $("#detailSourceBadge").className = `source source--${ipo.sourceStatus}`;
  $("#detailSourceBadge").textContent = {verified:"✓ VERIFIED",provisional:"PROVISIONAL",missing:"SOURCE MISSING"}[ipo.sourceStatus];
  $("#homeView").hidden = true;
  $("#detailView").hidden = false;
  window.scrollTo({top:0,behavior:"smooth"});
  history.replaceState(null,"",`#ipo/${ipo.id}`);
}
let toastTimer;
function toast(message){
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove("show"), 2400);
}

$("#topSearch").addEventListener("input",(event) => syncSearch(event.target.value));
$("#heroSearch").addEventListener("input",(event) => syncSearch(event.target.value));
$$("[data-home]").forEach((button) => button.addEventListener("click",showHome));
$$("[data-placeholder]").forEach((button) => button.addEventListener("click",() => toast(`${button.dataset.placeholder} is reserved for the next UI phase.`)));
$("#boardFilter").addEventListener("click",(event) => {
  if(!event.target.matches("button[data-board]")) return;
  state.board = event.target.dataset.board;
  setActive($$("#boardFilter button"),event.target);
  render();
});
$("#statusFilter").addEventListener("click",(event) => {
  if(!event.target.matches("button[data-status]")) return;
  state.status = event.target.dataset.status;
  setActive($$("#statusFilter button"),event.target);
  render();
});
$("#jumpSources").addEventListener("click",() => $("#documents").scrollIntoView({behavior:"smooth"}));
$("#jumpFinancials").addEventListener("click",() => $("#financials").scrollIntoView({behavior:"smooth"}));
$("#jumpTimeline").addEventListener("click",() => $("#timeline").scrollIntoView({behavior:"smooth"}));
$("#jumpDocuments").addEventListener("click",() => $("#documents").scrollIntoView({behavior:"smooth"}));

render();
if(location.hash.startsWith("#ipo/")) showDetail(location.hash.split("/")[1]);