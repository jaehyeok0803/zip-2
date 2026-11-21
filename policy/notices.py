"""Reviewed rounds with source-bound eligibility, kept separate from provider catalogues."""
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
import operator
import re

from policy.sources import fetch, SourceError

KST = timezone(timedelta(hours=9))
DISTRICTS = "강남구 강동구 강북구 강서구 관악구 광진구 구로구 금천구 노원구 도봉구 동대문구 동작구 마포구 서대문구 서초구 성동구 성북구 송파구 양천구 영등포구 용산구 은평구 종로구 중구 중랑구".split()
QUESTIONS = {
    "people":"현재 주민등록상 가구원 수",
    "moved":"선택한 자치구로 전입신고한 날짜",
    "fromOther":"다른 자치구에서 전입했나요?",
    "resident":"선택한 자치구에 현재 주민등록이 되어 있나요?",
    "age":"현재 만 나이",
    "personalIncome":"본인 세전 연소득 (만원)",
    "householdIncome":"가구 세전 연소득 (만원)",
    "noHome":"무주택 여부",
}
NOTICE = {
    "policyId":"ydp-center:256:2026","originalId":"256","round":"2026년 신규 전입 1인가구",
    "name":"영등포구 전입 1인가구 웰컴키트","agency":"영등포구1인가구지원센터",
    "scope":"자치구","regions":["영등포구"],"type":"주거 정착용 생필품",
    "benefit":"생활 필수품으로 구성된 웰컴키트","method":"온라인 또는 센터 방문 신청 후 방문 수령",
    "detailUrl":"https://ydp1in.or.kr/program/256","applyUrl":None,"homepage":None,
    "start":"2026-04-14","end":"2026-11-30","updatedAt":None,
    "rules":[("resident","eq","yes"),("fromOther","eq","yes"),("people","eq",1),
             ("age","ge",20),("moved","ge","2026-01-01")],
    "anchors":["2026년 1월 1일 이후","영등포구로 전입한 1인가구","만 20세 이상",
               "타 자치구에서","생활 필수품으로 구성된 웰컴키트","방문 수령",
               "프로그램 이용 이력이 없으신 경우에도","2026-04-14","2026-11-30"],
    # The organizer has explicitly closed this round. A stale "모집중" badge cannot reopen it.
    "closure":"모집마감",
    "openPattern":r"진행상태\s*모집중",
}
ROUNDS = [NOTICE]

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style"):
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ("script","style"):
            self.hidden = max(0,self.hidden-1)
    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())

def admission(notice, text, now):
    today = now.astimezone(KST).date().isoformat()
    if today < notice["start"]:
        return "접수 예정"
    if today > notice["end"]:
        return "기간 종료"
    if notice.get("closure") or re.search(r"\(모집마감\)|예산\s*소진으로.{0,15}종료|조기\s*종료되었습니다",text):
        return "조기 마감·예산 소진"
    if not all(part in text for part in notice["anchors"]):
        return "확인 불가"
    if notice.get("deadline") and now >= datetime.fromisoformat(notice["deadline"]):
        return "기간 종료"
    if not notice.get("deadline") and today == notice["end"]:
        return "확인 불가"
    return "접수 중" if re.search(notice["openPattern"],text) else "확인 불가"

def evaluate(notice, profile):
    results = []
    for field, op, target in notice["rules"]:
        value = profile.get(field)
        status = "확인 필요" if value is None else (
            "충족" if {"eq":operator.eq,"ge":operator.ge,"le":operator.le}[op](value,target) else "불충족")
        results.append(dict(field=field,label=QUESTIONS[field],status=status,sourceUrl=notice["detailUrl"]))
    return results

def verify_round(notice,profile):
    parser = VisibleText()
    parser.feed(fetch(notice["detailUrl"]))
    text = " ".join(" ".join(parser.parts).split())
    now = datetime.now(KST)
    if not all(p in text for p in notice["anchors"]):
        raise SourceError("모집 회차 또는 공고 내용 변경")
    status = admission(notice,text,now)
    item = {k:v for k,v in notice.items() if k not in ("rules","anchors","closure","openPattern")}
    item.update(status=status,statusCheckedAt=now.isoformat(),fetchedAt=now.isoformat(),
                sourceUrl=notice["detailUrl"],findings=evaluate(notice,profile),
                evidence=notice["anchors"],statusEvidence=notice.get("closure") or status)
    return item

