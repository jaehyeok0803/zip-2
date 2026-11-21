const state = {
  page: 'home',
  selectedDistrict: 'yeongdeungpo',
  compareDistricts: [],
  selectedSupport: 'loan',
  form: {
    deposit: '1000',
    monthly: '60',
    trip: 'commute',
    destinationName: '연세대학교 의과대학 강남세브란스병원',
    destinationAddress: '서울 강남구 언주로 211',
    mode: '대중교통',
    maxTime: '60',
    priority: '이동시간',
    priorities: ['주거비','이동시간','생활 편의시설'],
  },
  eligibility: {
    age: '',
    house: '',
    income: ''
  }
};

const districts = {
  yeongdeungpo: {
    name:'영등포구', total:'56.5', housing:'19.1', transport:'미평가', facilities:'94.0',
    housingLabel:'예산 충족 63 / 330건',
    facilitiesLabel:'2026. 11. 21. 집계 · 서울 25개 자치구 내 시설 수 순위 · 편의점 517곳 · 5위 (25점) · 대형마트 5곳 · 3위 (20점) · 약국 288곳 · 5위 (25점) · 병의원 860곳 · 6위 (24점)',
    support:'확인된 자치구 자체 공고가 없어요',
    pins:{x:50,y:56}
  },
  gwanak: {name:'관악구', total:'54.3', housing:'22.8', transport:'미평가', facilities:'86.2', housingLabel:'예산 충족 58 / 290건', facilitiesLabel:'서울대입구역 중심 생활 편의 예시', support:'관악구 청년 월세 지원 예시', pins:{x:58,y:63}},
  songpa: {name:'송파구', total:'51.7', housing:'16.4', transport:'미평가', facilities:'90.1', housingLabel:'예산 충족 47 / 260건', facilitiesLabel:'잠실역 중심 생활 편의 예시', support:'송파구 청년 사업 예시', pins:{x:73,y:50}},
  dongdaemun:{name:'동대문구', total:'49.8', housing:'20.6', transport:'미평가', facilities:'81.0', housingLabel:'예산 충족 41 / 210건', facilitiesLabel:'청량리역 중심 생활 편의 예시', support:'동대문구 공고 예시', pins:{x:67,y:40}},
  seocho:{name:'서초구', total:'49.3', housing:'13.2', transport:'미평가', facilities:'92.0', housingLabel:'예산 충족 31 / 184건', facilitiesLabel:'강남권 생활 편의 예시', support:'서초구 사업 예시', pins:{x:66,y:60}},
  dongjak:{name:'동작구', total:'34.2', housing:'11.3', transport:'미평가', facilities:'79.2', housingLabel:'예산 충족 25 / 140건', facilitiesLabel:'노량진 생활 편의 예시', support:'동작구 사업 예시', pins:{x:46,y:57}},
  gangnam:{name:'강남구', total:'46.1', housing:'10.0', transport:'미평가', facilities:'95.0', housingLabel:'예산 충족 19 / 130건', facilitiesLabel:'강남역 생활 편의 예시', support:'강남구 사업 예시', pins:{x:76,y:59}},
  gwangjin:{name:'광진구', total:'41.8', housing:'12.9', transport:'미평가', facilities:'88.7', housingLabel:'예산 충족 23 / 158건', facilitiesLabel:'건대입구 생활 편의 예시', support:'광진구 사업 예시', pins:{x:79,y:46}},
  jung:{name:'중구', total:'39.4', housing:'14.5', transport:'미평가', facilities:'83.1', housingLabel:'예산 충족 28 / 176건', facilitiesLabel:'을지로 생활 편의 예시', support:'중구 사업 예시', pins:{x:59,y:44}},
  eunpyeong:{name:'은평구', total:'40.2', housing:'18.1', transport:'미평가', facilities:'75.4', housingLabel:'예산 충족 32 / 196건', facilitiesLabel:'연신내 생활 편의 예시', support:'은평구 사업 예시', pins:{x:40,y:36}}
};

const resultRanking = ['yeongdeungpo','gwanak','songpa'];
const mapChips = ['yeongdeungpo','gwanak','songpa','dongdaemun','seocho','eunpyeong','gangnam','gwangjin','jung','dongjak'];

function logoHTML(){
  return `<button class="logo" data-go="home" aria-label="메인으로 이동">24<span class="roof">⌂</span>zip</button>`;
}

function appFrame(inner){
  return `
    <div class="screen">
      <div class="card-shell">
        <div class="app-header">
          ${logoHTML()}
          <div class="header-right">서울 청년 주거 가이드</div>
        </div>
        <div class="page-body">${inner}</div>
      </div>
      <div class="footer-note">24.zip · 프로토타입 &nbsp; 주거비는 서울시 거래 표본, 이동시간은 실제 경로 기준입니다. 주거지원은 공식 공고에서 신청 조건을 확인합니다.</div>
    </div>`;
}

function heroArt(){
  const leaves = Array.from({length:26}).map((_,i)=>{
    const x = 180 + (i*22)%280;
    const y = 22 + Math.floor(i/2)*12;
    const r = i%2===0 ? 24 : -22;
    return `<span class="leaf" style="left:${x}px;top:${y}px;transform:rotate(${r}deg)"></span>`;
  }).join('');
  const village = [0,82,156,240,314,388].map((x,i)=>`<span class="v-house" style="left:${x}px;height:${40 + (i%3)*8}px"></span>`).join('');
  return `
    <div class="hero-stage">
      <div class="hero-sky"></div>
      <div class="hero-branch"></div>
      ${leaves}
      <span class="hero-cloud cloud1"></span>
      <span class="hero-cloud cloud2"></span>
      <span class="hero-cloud cloud3"></span>
      <div class="hill"></div>
      <div class="hero-tower"></div>
      <div class="hero-tower tower-small"></div>
      <div class="hero-village">${village}</div>
      <div class="hero-houses">
        <div class="hero-house house-main"><span class="stairs"></span></div>
        <div class="hero-house house-side"></div>
      </div>
      <div class="hero-plants"></div>
      <div class="house-row"></div>
    </div>`;
}

function renderHome(){
  return `
    <div class="home-screen">
      <section class="home-hero">
        <div class="home-layout">
          <div class="home-copy">
            <div class="home-brand">24<span class="roof">⌂</span>zip</div>
            <h1 class="home-title">서울에서 살 곳을 비교하고,<br>주거지원 조건도 확인해요</h1>
            <p class="home-desc">예산과 이동 조건에 맞는 서울 자치구를 비교하고, 관심 있는 주거지원사업의 신청 자격을 확인해 보세요.</p>
            <button class="primary-btn home-cta" data-go="housing">추천 조건 입력하기 <span>→</span></button>
          </div>
          ${heroArt()}
        </div>
      </section>
      <div class="home-footer">
        <span>24.zip · 프로토타입</span>
        <span>주거비는 서울시 거래 표본, 이동시간은 실제 경로 기준입니다. 주거지원은 공식 공고에서 신청 조건을 확인합니다.</span>
      </div>
    </div>`;
}

function summaryList(){
  return `
    <div class="summary-item"><b>최대 보증금 ·</b> <span data-budget-label="deposit">${state.form.deposit === '' ? '미입력' : Number(state.form.deposit).toLocaleString('ko-KR')+'만 원'}</span></div>
    <div class="summary-item"><b>최대 월세 ·</b> <span data-budget-label="monthly">${state.form.monthly === '' ? '미입력' : Number(state.form.monthly).toLocaleString('ko-KR')+'만 원'}</span> (관리비 제외)</div>
    <div class="summary-item"><b>목적지 ·</b> 통근 / ${state.form.destinationName}</div>
    <div class="summary-item"><b>이동 수단 ·</b> ${state.form.mode}</div>
    <div class="summary-item"><b>최대 이동시간 ·</b> ${state.form.maxTime}분</div>
    <div class="summary-item"><b>1순위 조건 ·</b> ${state.form.priority}</div>
    <div class="summary-item"><b>중요 조건 ·</b> 주거비, 이동시간 (1순위), 생활 편의시설</div>`;
}

function renderHousing(){
  return appFrame(`
    <div class="back-row"><button class="back-btn" data-go="home">← 뒤로가기</button></div>
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap">
      <div>
        <h1 class="page-title">주거 조건 입력</h1>
        <p class="page-desc">예산과 이동 조건을 알려주면, 내게 맞는 동네와 관련 주거지원을 함께 보여드려요.</p>
      </div>
      <div class="top-switch">임시 · 이동시간 조회 <span class="switch-box"></span> OFF</div>
    </div>

    <div class="two-col" style="margin-top:26px">
      <div class="stack">
        <section class="section-card">
          <h2 class="section-title">예산</h2>
          <div class="form-grid two">
            <div class="field">
              <label>최대 보증금</label>
              <div class="input-wrap"><input class="input" data-budget="deposit" type="number" min="0" step="any" value="${esc(state.form.deposit)}" /><span class="suffix">만원</span></div>
            </div>
            <div class="field">
              <label>최대 월세</label>
              <div class="input-wrap"><input class="input" data-budget="monthly" type="number" min="0" step="any" value="${esc(state.form.monthly)}" /><span class="suffix">만원</span></div>
              <div class="note">월세만 입력해 주세요. 관리비는 포함하지 않아요. 서울시 전월세 거래 자료에는 관리비가 제공되지 않습니다.</div>
            </div>
          </div>
        </section>

        <section class="section-card">
          <h2 class="section-title">이동</h2>
          <div class="field" style="margin-bottom:18px">
            <label>이동 목적</label>
            <div class="segment-row">
              <button class="segment active">통근</button>
              <button class="segment">통학</button>
              <button class="segment">목적지 없음</button>
            </div>
          </div>
          <div class="choice-box">
            <strong>선택한 목적지 · ${state.form.destinationName}</strong><br>${state.form.destinationAddress}
          </div>
          <div class="inline-actions" style="margin-top:10px"><button class="mini-btn">변경</button></div>
          <div style="height:1px;background:#d3dceb;margin:18px 0"></div>
          <div class="field" style="margin-bottom:18px">
            <label>이동 수단</label>
            <div class="segment-row">
              <button class="segment active">대중교통</button>
              <button class="segment">도보</button>
              <button class="segment">자가용</button>
            </div>
          </div>
          <div class="field">
            <label>최대 허용 이동시간</label>
            <div class="segment-row four">
              <button class="segment">30분</button>
              <button class="segment">45분</button>
              <button class="segment active">60분</button>
              <button class="segment">직접 입력</button>
            </div>
            <div class="note">예상 이동시간은 실제 경로 조회 후 추천 결과와 지도 비교에서 확인할 수 있어요.</div>
          </div>
        </section>

        <section class="section-card">
          <h2 class="section-title">추천 우선순위</h2>
          <p class="subtle">세 가지 조건을 모두 평가합니다. 가장 중요하게 생각하는 조건을 선택해 주세요.</p>
          <div class="priority-row">
            <button class="priority-card">주거비</button>
            <button class="priority-card active"><span class="check">✓</span> 이동시간</button>
            <button class="priority-card">생활 편의시설</button>
          </div>
          <div class="note">생활 편의시설은 서울 25개 자치구의 시설 수 순위를 기준으로 평가합니다.</div>
        </section>
      </div>
      <aside class="summary-card">
        <h3>입력 조건 확인</h3>
        ${summaryList()}
        <button class="primary-btn full" data-go="results">추천 결과 보기 <span>→</span></button>
      </aside>
    </div>
  `);
}

function resultsConditions(){
  return `
    <div class="conditions-bar">
      <div class="cond"><small>최대 보증금</small><b><span data-budget-label="deposit">${state.form.deposit === '' ? '미입력' : Number(state.form.deposit).toLocaleString('ko-KR')+'만 원'}</span> 이하</b><div class="note">월세는 관리비 제외</div></div>
      <div class="cond"><small>최대 월세</small><b><span data-budget-label="monthly">${state.form.monthly === '' ? '미입력' : Number(state.form.monthly).toLocaleString('ko-KR')+'만 원'}</span> 이하</b></div>
      <div class="cond"><small>이동 목적지</small><b>${state.form.destinationName}</b></div>
      <div class="cond"><small>추천 우선순위</small><b>${state.form.priority}</b></div>
      <div class="cond"><small>이동 조건</small><b>대중교통 · 허용 60분</b></div>
    </div>`;
}

function renderResults(){
  const d = districts[state.selectedDistrict];
  return appFrame(`
    <div class="back-row"><button class="back-btn" data-go="housing">← 뒤로가기</button></div>
    <div class="results-top">
      <div>
        <h1 class="page-title" style="font-size:32px;margin-bottom:8px">내 조건에 맞는 서울 자치구</h1>
        <p class="page-desc" style="font-size:20px">확인된 자료를 바탕으로 자치구를 비교해 보세요.</p>
      </div>
      <div class="top-actions">
        <button class="primary-btn" data-go="map">🗺 지도에서 비교</button>
        <button class="primary-btn" data-go="housing">⚙ 주거 조건 수정</button>
      </div>
    </div>

    ${resultsConditions()}

    <div class="results-layout">
      <aside class="side-list">
        <h3>☷ 추천 자치구</h3>
        ${resultRanking.map((id,i)=>{
          const item = districts[id];
          return `<div class="rank-item ${id===state.selectedDistrict?'active':''}" data-district="${id}">
            <div class="rank-badge">${i+1}위</div>
            <div>
              <div class="rank-name">${item.name}</div>
              <div><span class="rank-score">${item.total} / 100</span><span class="rank-caption">부분 평가</span></div>
            </div>
            <div style="font-size:24px;color:#5d77a4">›</div>
          </div>`;
        }).join('')}
        <button class="more-btn">다른 자치구 7곳 보기 ▾</button>
      </aside>

      <section class="detail-panel">
        <div class="detail-head">
          <h2>${d.name}</h2>
          <div class="score-box"><strong>${d.total} / 100</strong><small>부분 평가 · 임시</small></div>
        </div>

        <div class="metric-grid">
          <article class="metric-card">
            <h4>⌂ 주거비</h4>
            <div class="metric-number">${d.housing}</div>
            <div class="metric-sub">/ 100점</div>
            <div class="progress"><span style="width:${d.housing}%"></span></div>
            <div class="metric-sub">${d.housingLabel}</div>
            <div class="fold-row">▸ 근거 보기</div>
          </article>
          <article class="metric-card">
            <h4>🚇 이동시간</h4>
            <div class="metric-number">—</div>
            <div class="metric-sub">미평가</div>
            <div class="progress"><span style="width:0%"></span></div>
            <div class="metric-sub">이동시간 조회 OFF</div>
            <div class="pill-inline">1순위 조건</div>
          </article>
          <article class="metric-card">
            <h4>🏢 편의시설</h4>
            <div class="metric-number">${d.facilities}</div>
            <div class="metric-sub">/ 100점</div>
            <div class="progress"><span style="width:${d.facilities}%"></span></div>
            <div class="metric-sub">${d.facilitiesLabel}</div>
          </article>
        </div>

        <div class="accordion"><summary>적용 가중치</summary></div>

        <div class="support-section">
          ${policyEntry(d.name)}</div>
        <details class="accordion">
          <summary>점수 계산 기준</summary>
          <div class="accordion-content">사용자가 입력한 보증금과 월세를 기준으로 조건 이하 매물 수를 반영하고, 편의시설 점수와 우선순위 가중치를 적용하는 화면 구조 예시입니다.</div>
        </details>
      </section>
    </div>
  `);
}

function mapPins(){
  return mapChips.map(id=>{
    const d = districts[id];
    const active = state.selectedDistrict===id;
    const name = `${d.name} ${d.total}`;
    return `<button class="map-pin ${active?'active':''}" style="left:${d.pins.x}%;top:${d.pins.y}%" data-mapdistrict="${id}">${name}</button>`;
  }).join('') + `<button class="map-pin destination" style="left:78%;top:56%">주요 목적지</button>`;
}

function renderMap(){
  const d = districts[state.selectedDistrict];
  return appFrame(`
    <div class="back-row"><button class="back-btn" data-go="results">← 뒤로가기</button></div>
    <div class="page-kicker">03 · 지도 비교</div>
    <h1 class="page-title" style="font-size:32px">지도에서 동네 비교</h1>
    <p class="page-desc" style="font-size:20px">지도에서 자치구를 골라 최대 두 곳을 비교해 보세요.</p>

    <div class="section-card" style="margin-top:22px">
      <div class="info-overview">
        <div>
          <h2 class="section-title" style="margin-bottom:0">내 조건</h2>
          <div class="overview-left" style="margin-top:14px">
            <div class="overview-box"><small>최대 보증금</small><strong><span data-budget-label="deposit">${state.form.deposit === '' ? '미입력' : Number(state.form.deposit).toLocaleString('ko-KR')+'만 원'}</span></strong></div>
            <div class="overview-box"><small>최대 월세</small><strong><span data-budget-label="monthly">${state.form.monthly === '' ? '미입력' : Number(state.form.monthly).toLocaleString('ko-KR')+'만 원'}</span></strong></div>
            <div class="overview-box">
              <strong style="font-size:18px">📍 ${state.form.destinationName}</strong>
              <div class="pill-inline" style="margin-top:8px">대중교통 · 허용 60분</div>
              <div class="pill-inline">추천 1순위 <strong style="font-size:16px">${state.form.priority}</strong></div>
              <div class="note" style="margin-top:8px">월세는 관리비 제외</div>
            </div>
          </div>
        </div>
        <button class="ghost-btn" data-go="housing">조건 수정</button>
      </div>

      <div class="map-tools">
        <button class="ghost-btn">목적지 위치 보기</button>
        <button class="ghost-btn">주변 버스정류장 보기</button>
      </div>

      <div class="map-frame">
        <div class="map-box">
          <div class="fake-map"></div>
          <div class="river"></div>
          <div class="road r1"></div>
          <div class="road r2"></div>
          <div class="road r3"></div>
          <div class="road r4"></div>
          ${mapPins()}
        </div>
        <aside class="map-sidebar">
          <h3>선택 지역 요약</h3>
          <div class="summary-score"><strong>${d.name}</strong><br><span style="font-size:48px">${d.total}</span> / 100점</div>
          <div class="note" style="margin-bottom:12px">부분 평가 · 임시</div>
          <div class="line-list">
            <div class="line-item"><span>주거비</span><strong>${d.housing} / 100</strong></div>
            <div class="line-item"><span>이동시간</span><strong>${d.transport}</strong></div>
            <div class="line-item"><span>생활 편의시설</span><strong>${d.facilities} / 100</strong></div>
          </div>
          <div class="note" style="margin-top:14px">대중교통 · 이동시간 조회 OFF</div>
          <button class="large-primary">비교 대상에 추가</button>
        </aside>
      </div>

      <div class="note" style="font-size:18px;margin:12px 0 0">현재 평가 점수 · 100점 만점 · 부분 평가는 임시 점수</div>

      <div class="compare-box">
        <h3>비교 대상 0/2</h3>
        <div class="subtle" style="font-size:18px">지도 마커는 상세 확인, 아래 구 이름은 비교 대상 선택이에요.</div>
        <div class="chip-list">
          ${mapChips.map(id=>`<button class="chip" data-mapdistrict="${id}">${districts[id].name}</button>`).join('')}
        </div>
        <div class="subtle" style="font-size:18px">비교할 자치구를 최대 두 곳 선택해 주세요.</div>
      </div>

      <div style="height:1px;background:#d4ddec;margin:24px 0"></div>

      <div>
        <h3 class="section-title" style="font-size:24px">${d.name} 상세 정보</h3>
        <div class="fold-row">▸ 점수 근거 보기</div>

        <div class="support-section">${policyEntry(d.name)}</div>
        <button class="primary-btn full return-btn" data-go="results">추천 결과로 돌아가기</button>
      </div>
    </div>
  `);
}

function render(){
  const app = document.getElementById('app');
  if(state.page === 'home') app.innerHTML = renderHome();
  if(state.page === 'housing') app.innerHTML = renderHousing();
  if(state.page === 'results') app.innerHTML = renderResults();
  if(state.page === 'map') app.innerHTML = renderMap();
  if(state.page === 'qualify') app.innerHTML = renderQualify();
  if(state.page === 'decision') app.innerHTML = renderDecision();
}

document.addEventListener('click', (e)=>{
  const go = e.target.closest('[data-go]');
  if(go){
    if(go.dataset.go==='qualify' && ['map','results'].includes(state.page)){
      if(policyState.district!==districts[state.selectedDistrict].name){
        for(const key of ['resident','moved','fromOther']) delete policyState.answers[key];
      }
      enterPolicy();
    }
    if(state.page==='decision') {policyState.version++;policyState.controller?.abort();policyState.busy=false;}
    state.page = go.dataset.go; render(); return; }
  const district = e.target.closest('[data-district]');
  if(district){ state.selectedDistrict = district.dataset.district; render(); return; }
  const mapd = e.target.closest('[data-mapdistrict]');
  if(mapd){ state.selectedDistrict = mapd.dataset.mapdistrict; render(); }
});

render();
