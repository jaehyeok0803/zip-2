const policyDistricts = '강남구 강동구 강북구 강서구 관악구 광진구 구로구 금천구 노원구 도봉구 동대문구 동작구 마포구 서대문구 서초구 성동구 성북구 송파구 양천구 영등포구 용산구 은평구 종로구 중구 중랑구'.split(' ');
const policyState = { answers:{}, district:'', result:null, version:0, controller:null, busy:false, error:'' };
const fieldDefs = {
  age:['만 나이','number'], personalIncome:['본인 세전 연소득 (만원)','number'],
  noHome:['무주택 여부', {yes:'무주택',no:'주택 소유'}],
  single:['현재 또는 독립 후 1인가구인가요?',{yes:'예',no:'아니요'}],
  people:['현재 주민등록상 가구원 수','number'],moved:['선택 지역 전입신고일','date'],
  fromOther:['다른 자치구에서 전입했나요?',{yes:'예',no:'아니요'}],
  householdIncome:['가구 세전 연소득 (만원)','number']
};
function esc(s) { return String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function options(items,value) {
  return Object.entries(items).map(([k,v])=>`<option value="${esc(k)}" ${k===value?'selected':''}>${esc(v)}</option>`).join('');
}
function policyField(k) {
  const [label,type]=fieldDefs[k], v=policyState.answers[k] ?? '';
  const control = typeof type==='object'
    ? `<select data-answer="${k}" id="p-${k}"><option value="">미입력</option>${options(type,v)}</select>`
    : `<input data-answer="${k}" id="p-${k}" type="${type}" min="0" step="${['age','people'].includes(k)?'1':'any'}" value="${esc(v)}">`;
  return `<div class="field-vertical"><label for="p-${k}">${esc(label)}</label>${control}</div>`;
}
function policyEntry(name) {
  return `<div class="support-block"><h3>주거지원 정책</h3><div class="support-card">${esc(name)}에서 이용할 수 있는 자치구·서울시·중앙부처 사업을 확인해 보세요.</div></div><div class="cta-stack"><button class="outline-btn" data-go="qualify">내 조건 확인하기</button></div>`;
}
function enterPolicy() {
  policyState.district = districts[state.selectedDistrict].name;
  clearPolicy();
}
function clearPolicy() {
  policyState.version++;
  policyState.controller?.abort();
  policyState.result=null; policyState.error=''; policyState.busy=false;
}
function renderQualify() {
  const keys = new Set(['age','personalIncome','noHome',...Object.keys(policyState.result?.requiredFields || {})]);
  const money = v => v === '' ? '미입력' : Number(v).toLocaleString('ko-KR')+'만 원';
  return appFrame(`<button class="back-btn" data-go="results">← 추천 결과</button><h1 class="page-title">공공임대·주거비·청년 생활지원금 조건</h1>
    <section class="qual-card"><div class="form-vertical"><div class="field-vertical"><label for="policy-district">현재 살고 있거나 전입할 자치구</label>
    <select id="policy-district">${options(Object.fromEntries(policyDistricts.map(d=>[d,d])),policyState.district)}</select></div>
    <p>앞에서 입력한 최대 예산 · 보증금 ${money(state.form.deposit)} / 월세 ${money(state.form.monthly)}</p>
    <form id="policy-form" class="form-vertical">${[...keys].filter(k=>fieldDefs[k]).map(policyField).join('')}
    <button class="primary-btn full">신청 조건 확인하기</button></form></div></section>`);
}
function currentProfile() {
  const p = {district:policyState.district, locationIntent:"yes", ...policyState.answers};
  for(const k of ['deposit','monthly']) p[k]=state.form[k] === '' ? null : Number(state.form[k]);
  return p;
}
async function policyRequest(signal,id) {
  if(location.protocol==='file:') throw Error('정책 조회는 Vercel 배포 주소 또는 로컬 API 서버에서 이용해 주세요.');
  const res=await fetch('/api/policies',{method:'POST',headers:{'Content-Type':'application/json'},cache:'no-store',signal,
    body:JSON.stringify({profile:currentProfile(),recheckId:id})});
  if(!res.headers.get('content-type')?.includes('application/json')) throw Error('정책 API에 연결할 수 없어요. 배포 폴더에 api/policies.py가 있는지 확인해 주세요.');
  const data=await res.json();
  if(!data.sources) throw Error(data.error || '공식 자료를 조회하지 못했어요.');
  return data;
}
async function queryPolicy(id) {
  policyState.controller?.abort();
  const token=++policyState.version;
  const controller=new AbortController(); policyState.controller=controller;
  policyState.busy=true; policyState.error=''; state.page='decision'; render();
  try {
    const data=await policyRequest(controller.signal,id);
    if(token!==policyState.version || state.page!=='decision') return;
    if(id){
      const item=data.recommendations.find(p=>p.policyId===id);
      if(item) {
        const target=item.applyUrl||item.detailUrl||item.homepage;
        if(target && new URL(target).protocol==='https:'){location.assign(target);return;}
      }
      policyState.result=null;
      policyState.error='신청 경로를 다시 확인하지 못했어요. 현재 조건으로 다시 조회해 주세요.';
    } else { policyState.result=data; }
  } catch(e){
    if(token===policyState.version && e.name!=='AbortError'){policyState.result=null; policyState.error=e.message;}
  } finally {
    if(token===policyState.version){policyState.busy=false;if(state.page==='decision')render();}
  }
}
function policyCard(p) {
  const when=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',dateStyle:'medium',timeStyle:'short'}).format(new Date(p.statusCheckedAt));
  return `<article class="result-panel"><div class="page-kicker">${esc(p.scope)} · ${esc(p.agency)} · ${esc(p.round)}</div><h2>${esc(p.name)}</h2>
  <p><b>${esc(p.benefit)}</b></p><p>${esc(p.reason)} <small>(${esc(p.explanationSource)})</small></p>
  <p>${esc(p.start)} ~ ${esc(p.end)} · ${esc(p.status)}<br>접수 확인 ${esc(when)} (한국시간)</p><p>${esc(p.method)}</p>
  <details><summary>판정 근거</summary><p>${esc(p.statusEvidence)}</p><ul>${p.findings.map(f=>`<li>${esc(f.label)} · ${esc(f.status)}</li>`).join('')}</ul>
  <a href="${esc(p.sourceUrl)}" target="_blank" rel="noopener noreferrer">공식 근거 확인</a></details>
  <button class="primary-btn full" data-recheck="${esc(p.policyId)}">${p.applyUrl?'신청 페이지로 이동':p.detailUrl?'공식 안내 확인':'기관 홈페이지'}</button></article>`;
}
function renderDecision(){
  const r=policyState.result;
  let body='';
  if(policyState.busy)body='<p role="status">공식 공고와 현재 접수 상태를 확인하고 있어요…</p>';
  else if(policyState.error)body=`<p role="alert">${esc(policyState.error)}</p>`;
  else if(r){
    const messages={failed:'공식 자료를 조회하지 못했어요.',input:'아래 정보를 추가하면 신청 조건을 확인할 수 있어요.',
      empty:'현재 입력 조건과 접수 상태를 모두 확인한 주거·생활지원 사업이 없습니다.',results:'신청 조건과 접수 상태를 확인한 사업이에요.'};
    const cards=r.sources.flatMap(s=>[...(s.cards||[]),...(s.pending||[])].map(p=>({...p,agency:s.name})));
    const intro=r.state==='empty' && cards.length?'아래 사업에서 지원 대상과 신청 방법을 확인해 보세요.':messages[r.state];
    body=`<p>${intro}</p>${r.recommendations.map(policyCard).join('')}
    ${cards.length?`<h2>공공임대·주거비·청년 생활지원금 후보 · ${cards.length}건</h2>${cards.map(p=>`<article class="result-panel"><small>${esc(p.agency)}</small><h3>${esc(p.name)}</h3>
      <p>${esc(p.reason)}</p>${[['지원 내용',p.benefit],['지원 대상',p.target],['선정 기준',p.criteria],['신청 방법',p.method]].filter(([,v])=>v).map(([k,v])=>`<p><b>${k}</b> · ${esc(v)}</p>`).join('')}
      ${p.status?`<p>${esc(p.status)}</p>`:''}
      ${p.sourceUrl?`<a href="${esc(p.sourceUrl)}" target="_blank" rel="noopener noreferrer">${esc(p.linkLabel||'공식 상세 안내')}</a>`:''}
      ${p.applyUrl?` · <a href="${esc(p.applyUrl)}" target="_blank" rel="noopener noreferrer">신청 페이지</a>`:''}
      ${!p.sourceUrl&&!p.applyUrl?'공식 자료에 개별 링크가 없습니다.':''}</article>`).join('')}`:''}
    ${Object.keys(r.requiredFields).length?`<section class="support-card"><b>추가 입력 필요</b><p>${Object.values(r.requiredFields).map(esc).join(' · ')}</p><button class="outline-btn" data-go="qualify">정보 보완하기</button></section>`:''}
    <section class="support-card"><strong>${r.partial?'일부 출처 조회 제한':'조회한 공식 출처'}</strong><ul>${r.sources.map(s=>`<li>${esc(s.name)} · ${s.state==='ok'?esc(s.detailWarning||(s.detailErrors?'일부 조회 제한':'조회 성공')):esc(s.message)}${s.records!==undefined?` (목록 ${s.records}건 · 지원 후보 ${s.discovered}건 · 상세 확인 ${s.detailRead}건 · 내 조건으로 표시 ${s.cards?.length||0}건)`:''}</li>`).join('')}</ul></section>
    ${r.sources.filter(s=>s.myhomeCount!==undefined).map(s=>`<p>마이홈에서 확인한 서울 지역 공고 ${s.myhomeCount}건${s.detailErrors?' · 일부 목록 또는 상세 조회 제한':''}</p>`).join('')}
    ${r.excluded.length?`<details><summary>접수 상태로 제외한 공고</summary>${r.excluded.map(x=>`<p>${esc(x.name)} · ${esc(x.status)}</p>`).join('')}</details>`:''}`;
  }
  return appFrame(`<button class="back-btn" data-go="qualify">← 조건 수정</button><h1 class="page-title">${esc(policyState.district)} 공공임대·주거비·청년 생활지원금 확인 결과</h1>
    <section aria-live="polite">${body}</section>${policyState.busy?'':'<button class="outline-btn" data-policy-retry>다시 조회하기</button>'}`);
}
document.addEventListener('input',e=>{
  const k=e.target.dataset.answer;
  if(k)policyState.answers[k]=e.target.value===''?null:e.target.type==='number'?e.target.valueAsNumber:e.target.value;
  const b=e.target.dataset.budget;
  if(b){state.form[b]=e.target.value;const out=document.querySelector('[data-budget-label="'+b+'"]');if(out)out.textContent=e.target.value===''?'미입력':Number(e.target.value).toLocaleString('ko-KR')+'만 원';}
});
document.addEventListener('change',e=>{
  if(e.target.id==='policy-district'){
    policyState.district=e.target.value;for(const k of ['moved','fromOther','resident'])delete policyState.answers[k];
    clearPolicy();render();
  }
});
document.addEventListener('submit',e=>{if(e.target.id==='policy-form'){e.preventDefault();queryPolicy();}});
document.addEventListener('click',e=>{
  const link=e.target.closest('[data-recheck]');if(link)queryPolicy(link.dataset.recheck);
  else if(e.target.closest('[data-policy-retry]'))queryPolicy();
});

