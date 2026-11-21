from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import os
import math
import re
from policy import sources
from policy.notices import DISTRICTS, QUESTIONS, KST
from policy.explain import explain
from policy.discovery import summarize, catalogue_cards
from policy.lh import listings
from policy.central_search import search
from policy.finance import loan_review

NUMBERS = {"age":130,"personalIncome":1e10,"householdIncome":1e10,"deposit":1e10,"monthly":1e10,"people":100}
ENUMS = {"locationIntent":{"yes","no"},"resident":{"yes","planned"},"noHome":{"yes","no"},"single":{"yes","no"},"fromOther":{"yes","no"}}

def validate(value):
    if not isinstance(value,dict) or value.get("district") not in DISTRICTS:
        raise ValueError("서울 자치구를 선택해 주세요.")
    result = {"district":value["district"]}
    for k,v in value.items():
        if k=="district" or v is None or v=="":
            continue
        if k in NUMBERS:
            if type(v) not in (float,int) or not math.isfinite(v) or not 0 <= v <= NUMBERS[k] or (k in ("age","people") and int(v)!=v) or (k=="people" and v==0):
                raise ValueError("숫자와 단위를 확인해 주세요.")
        elif k in ENUMS:
            if not isinstance(v,str) or v not in ENUMS[k]:
                raise ValueError("선택 항목을 확인해 주세요.")
        elif k=="moved":
            if not isinstance(v,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",v) or date.fromisoformat(v)>datetime.now(KST).date():
                raise ValueError("전입신고 날짜를 확인해 주세요.")
        else:
            raise ValueError("지원하지 않는 입력 항목입니다.")
        result[k]=v
    return result

def catalogue(provider,reader,profile):
    data = sources.cached(provider,reader)
    warning = ""
    if provider=="seoul":
        data,warning=data
    if provider=="central":
        data = {key:{"list":[row],"detail":[]} for key,row in data.items()}
    cards = catalogue_cards(data,profile,provider)
    counts = summarize("seoul",data)
    return [],dict(detailWarning=warning,records=len(data),cards=cards,pending=[],**counts)

def lookup(profile,only=None):
    jobs = {"서울시·자치구 복지서비스":lambda:catalogue("seoul",sources.seoul,profile),
            "서울주거포털":lambda:loan_review(profile)}
    if not only:
        jobs["LH · 서울 공공임대 공고"] = lambda:sources.cached("lh-seoul",listings)
        jobs["중앙부처 · 마이홈 공식 공고"] = lambda:search(profile["district"])
    if os.getenv("CENTRAL_WELFARE_API_KEY"):
        jobs["중앙부처 복지서비스"] = lambda:catalogue("central",sources.national,profile)
    verified, needs, sources_info, excluded = {},{},[],[]
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [(name,pool.submit(job)) for name,job in jobs.items()]
        for name,future in futures:
            try:
                items,counts = future.result()
                sources_info.append(dict(name=name,state="ok",**counts))
            except Exception as error:
                msg = str(error) if isinstance(error,sources.SourceError) else "공급자 응답 형식 또는 연결 확인 필요"
                sources_info.append(dict(name=name,state="unconnected" if msg=="미연결" else "error",message=msg))
                continue
            for item in items:
                pid = item["policyId"]
                if only and pid!=only:
                    continue
                if profile["district"] not in item["regions"] or item["status"]!="접수 중":
                    excluded.append({"name":item["name"],"status":item["status"],"sourceUrl":item["sourceUrl"]})
                    continue
                findings = item["findings"]
                if not findings or any(r["status"]=="불충족" for r in findings):
                    continue
                missing = [r["field"] for r in findings if r["status"]=="확인 필요"]
                if "resident" in missing:
                    continue
                if missing:
                    for field in missing:
                        needs[field] = QUESTIONS[field]
                    continue
                if not only:
                    item["reason"],item["explanationSource"] = explain(item)
                verified[pid]=item
    success = sum(s["state"]=="ok" for s in sources_info)
    state = "results" if verified else "input" if needs else "failed" if not success else "empty"
    return dict(state=state,partial=success<len(sources_info) or any(s.get("detailWarning") or s.get("detailErrors") or s.get("detailDeferred") for s in sources_info),district=profile["district"],
                recommendations=list(verified.values()),requiredFields=needs,sources=sources_info,excluded=excluded)

