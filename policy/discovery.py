"""Screen catalogue content for review. Discovery never implies eligibility or open intake."""
import re
from html import unescape
from urllib.parse import urlsplit
from policy.notices import DISTRICTS
from concurrent.futures import ThreadPoolExecutor
from policy import sources

TITLE = {"servnm","wlfareinfonm","서비스명","사업명"}
BENEFIT = {"alwservcn","sprtcn","servdgst","wlfareinfooutlcn","지원내용","서비스요약"}
PAYMENT = r"(?:의|을|를)?(?:일부|전액|실비|최대[0-9,]+만원)?(?:를|을)?(?:지원|보조|지급|환급|감면|대납|보전)"
HOUSING_COST = re.compile(
    r"주거급여|주택바우처|주거비바우처|임차급여|"
    r"(?:월세|임대료|임차료|주거비|이사비(?:용)?|중개보수(?:비)?|복비|집수리비|주택수리비|"
    r"(?:임차|전세|임대)보증금(?:반환보증보증료|반환보증료|대출이자|이자)?|"
    r"(?:주택|전월세|전세|주거)대출이자|전세보증료)" + PAYMENT)
YOUTH_CASH = re.compile(r"청년(?:기본소득|수당|생활안정자금|생활안정지원금)|"
                       r"(?:생활비|생활안정비|생활지원금|생활안정지원금|자립수당|자립정착금|기본소득)(?:$|사업|매월|월|연|[0-9]|"+PAYMENT+r")")
RESTRICTED = re.compile(r"입원|의료|진료|치료|간병|수술|병원|건강검진|직업훈련|직무교육|구직활동비|면접비|응시료|학자금|등록금")
REFERENCE = re.compile(r"중복|제외|미지원|지원하지않|(?:주거급여|청년수당)(?:수급자|수급중|수혜자)")

RENTAL = re.compile(r"공공임대|임대주택|국민임대|영구임대|전세임대|매입임대|행복주택|청년안심주택|장기전세|공공지원민간임대")
INTAKE = re.compile(r"(?:예비)?입주자?(?:를)?(?:수시|추가|상시|예비)?모집|입주신청(?:접수)?")
SUPPLY = re.compile(r"(?:"+RENTAL.pattern+r")(?:주택)?(?:을|를)?(?:공급|제공|입주지원)")

def candidate(record):
    rows = record.get("list", []) + record.get("detail", []) if "list" in record else [record]
    names, benefits, targets = [], [], []
    for row in rows:
        for key, value in row.items():
            if not isinstance(value,str):
                continue
            key = key.lower().replace("_","")
            text = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "；", unescape(value)))
            if key in TITLE:
                names.append(text)
            elif key in BENEFIT:
                benefits.extend(re.split(r"[。.;；○ㅇ]",text))
            elif key in {"sprttrgtcn","tgtrdtlcn","sporttrgetcn","servtgtcn","지원대상"}:
                targets.append(text)
    youth = any("청년" in t for t in names + targets)
    if any(RESTRICTED.search(t) for t in names):
        return False
    for text in names + benefits:
        if REFERENCE.search(text) or RESTRICTED.search(text):
            continue
        if SUPPLY.search(text) or (INTAKE.search(text) and any(RENTAL.search(t) for t in [text,*names])):
            return True
        if HOUSING_COST.search(text):
            return True
        if (youth or "청년" in text) and YOUTH_CASH.search(text):
            return True
    return False

def official_link(value):
    try:
        url = urlsplit(value)
        host = url.hostname or ""
        if (url.scheme in ("http","https") and not url.username and not url.password
                and (host.endswith(".go.kr") or host in {"apply.lh.or.kr","www.lh.or.kr","www.i-sh.co.kr"})):
            return value
    except ValueError:
        pass
    return ""

def catalogue_cards(records, profile, provider="seoul"):
    cards = []
    for identifier, record in records.items():
        if not candidate(record):
            continue
        fields = {}
        for row in record["list"] + record["detail"]:
            for key, raw in row.items():
                if isinstance(raw,str) and raw.strip():
                    key = key.lower().replace("_","")
                    value = " ".join(re.sub(r"<[^>]+>", " ", unescape(raw)).split())
                    if value:
                        fields.setdefault(key, []).append(value)
        def field(*keys):
            return next((" / ".join(dict.fromkeys(fields[k])) for k in keys if k in fields), "")
        name = field("servnm","wlfareinfonm","서비스명","사업명")
        area = field("sggnm","cggnm","signgunm","시군구명","자치구명","jurmdnm")
        districts = [d for d in DISTRICTS if d in (area or name)]
        if districts and profile["district"] not in districts:
            continue
        intake = field("rcritsttsnm","rcptsttsnm","접수상태","모집상태").replace(" ","")
        if intake in {"모집마감","접수마감","접수종료","기간종료","마감","종료"}:
            continue
        target = field("sprttrgtcn","tgtrdtlcn","sporttrgetcn","servtgtcn","지원대상")
        criteria = field("slctcritcn","slctcrtrcn","선정기준")
        reason = [profile["district"]+" 대상 지역" if districts else "세부 대상 지역 확인 필요"]
        exclude = False
        # Only exclude on standalone requirements. Exceptions and alternative groups need review.
        for line in (target,criteria):
            # Match simple conjunctive descriptions as well as bare field values.
            # Multi-group rules, exceptions and household-member ages need individual review.
            if re.search(r"또는|혹은|예외|제외|다만|특례|완화|우선|가점|이거나|중 하나|자녀|부모|배우자|가구원|장애|군복무|/|①|②",target+" "+criteria):
                continue
            ages = re.search(r"(?:만\s*)?(\d{1,3})\s*세?\s*(?:[~∼～–]|세?\s*이상\s*(?:부터\s*)?)\s*(?:만\s*)?(\d{1,3})\s*세\s*(?:이하)?",line)
            if ages and "age" in profile:
                low, high = map(int, ages.groups())
                if not low <= profile["age"] <= high:
                    exclude = True
                else:
                    reason.append("만 나이 일치")
            if re.search(r"무주택(?:자|\s*세대주|\s*청년)",line) and profile.get("noHome"):
                exclude |= profile["noHome"] == "no"
                if profile["noHome"] == "yes":
                    reason.append("무주택 조건 일치")
            income = re.search(r"본인\s*(?:세전\s*)?연소득\s*([\d,]+)\s*만\s*원\s*이하",line)
            if income and "personalIncome" in profile:
                exclude |= profile["personalIncome"] > int(income[1].replace(",",""))
                if not exclude:
                    reason.append("본인 연소득 조건 일치")
        if exclude:
            continue
        def link(*keys):
            return next((v for k in keys for v in fields.get(k,[]) if official_link(v)), "")
        detail = link("servdtllink","servdtlurl","wlfareinfodtlurl","상세조회url")
        if not detail and re.fullmatch(r"WLF\d+",identifier):
            detail = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId="+identifier+"&wlfareInfoReldBztpCd="+("01" if provider=="central" else "02")
        cards.append(dict(name=name or "복지서비스 "+identifier,reason=" · ".join(reason),
            benefit=field("alwservcn","sprtcn","servdgst","wlfareinfooutlcn","지원내용","서비스요약"),
            target=target,criteria=criteria,method=field("aplymthdcn","applmetcn","aplymthdnm","aplymtdcn","신청방법"),
            sourceUrl=detail,applyUrl=link("aplyurl","onlaplyurl","applyurl","신청url"),
            status="접수 여부와 세부 자격 확인 필요"))
    return cards

def summarize(provider,records):
    ids = [key for key,value in records.items() if candidate(value)]
    if provider=="seoul":
        return dict(discovered=len(ids),detailRead=sum(bool(records[i]["detail"]) for i in ids),detailErrors=0,detailDeferred=sum(not records[i]["detail"] for i in ids))
    # Bound work per request. Advertise deferred records separately from completed requests.
    def get(key):
        try:
            sources.cached("central:"+key,lambda:sources.national_detail(key))
            return True
        except Exception:
            return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        checked = sum(pool.map(get,ids[:8]))
    return dict(discovered=len(ids),detailRead=checked,detailErrors=min(8,len(ids))-checked,
                detailDeferred=max(0,len(ids)-8))

