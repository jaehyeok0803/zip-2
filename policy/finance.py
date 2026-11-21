from policy.contract import read
from policy.sources import SourceError
from policy.notices import evaluate

LOAN_URL = "https://housing.seoul.go.kr/site/main/content/sh01_040901"

def loan_review(profile):
    _, text = read(LOAN_URL)
    if not all(x in text for x in ("청년임차보증금이자지원사업","2026.6.5.","5천만원","만19~39세","임차보증금대출")):
        raise SourceError("금융지원 공고 변경 · 재검토 필요")
    criteria = {"detailUrl":LOAN_URL,"rules":[("age","ge",19),("age","le",39),("personalIncome","le",5000)]}
    findings = evaluate(criteria,profile)
    pending = []
    if all(f["status"]!="불충족" for f in findings):
        matching = sorted({f["label"] for f in findings if f["status"]=="충족"})
        reason = ("입력값과 일치한 항목: "+", ".join(matching)+". " if matching else "")
        pending.append(dict(name="청년 임차보증금 이자지원",sourceUrl=LOAN_URL,
            reason=reason+"대출이자의 일부를 지원하는 사업입니다. 현재 신규 접수 및 세부 요건 확인이 필요합니다."))
    return [],dict(pending=pending)

