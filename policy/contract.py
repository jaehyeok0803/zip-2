"""Check the city's application directory and the chosen district's current intake form."""
import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit, parse_qs
from policy.notices import KST, VisibleText, evaluate, QUESTIONS
from policy.sources import fetch, SourceError

PORTAL = "https://1in.seoul.go.kr/front/sport/sportView.do?sport_id=a97db018d11c44af845fd028fde7104c"
ANNUAL = "https://youth.seoul.go.kr/infoData/plcyInfo/view.do?key=2309150002&plcyBizId=20261021005400214222"
QUESTIONS.update(single="현재 또는 독립 후 1인가구인가요?", locationIntent="선택한 구에 거주 중이거나 전입 예정인가요?")

class Page(VisibleText):
    def __init__(self):
        super().__init__()
        self.links = []
        self.anchor = None
        self.next_step = False
        self.button = None
    def handle_starttag(self,tag,attrs):
        super().handle_starttag(tag,attrs)
        a = dict(attrs)
        if tag == "a":
            self.anchor = [a.get("href",""),[]]
        if tag == "button" and "disabled" not in a and a.get("aria-disabled") != "true":
            self.button = []
    def handle_data(self,data):
        super().handle_data(data)
        if self.anchor is not None:
            self.anchor[1].append(data)
        if self.button is not None:
            self.button.append(data)
    def handle_endtag(self,tag):
        super().handle_endtag(tag)
        if tag == "a" and self.anchor is not None:
            href, parts = self.anchor
            self.links.append((href, "".join("".join(parts).split())))
            self.anchor = None
        if tag == "button" and self.button is not None:
            self.next_step |= "".join(self.button).strip() == "다음"
            self.button = None

def read(url):
    page = Page()
    page.feed(fetch(url))
    return page, "".join("".join(page.parts).split())

def contract(profile):
    district = profile["district"]
    directory, text = read(PORTAL)
    if not all(x in text for x in ("전월세계약상담","집보기동행","서울시거주또는거주예정1인가구","독립가구예정인자포함")):
        raise SourceError("서울시 지원내용 또는 지원대상 변경")
    urls = {urljoin(PORTAL,h) for h,label in directory.links if label.startswith(district+"신청하기")}
    if len(urls) != 1:
        raise SourceError("선택 지역 신청 경로 확인 불가")
    url = urls.pop()
    parsed = urlsplit(url)
    bid = parse_qs(parsed.query).get("bsns_id",[""])[0]
    if parsed.netloc != "1in.seoul.go.kr" or parsed.path != "/front/bsns/bsnsApplcntStep1Page.do" or not re.fullmatch("[a-f0-9]{32}",bid):
        raise SourceError("신청 경로 변경")
    _, annual = read(ANNUAL)
    if not all(x in annual for x in ("2026전월세안심계약도움서비스운영","20260101~20261231")):
        raise SourceError("연도별 신청기간 확인 필요")
    form, contents = read(url)
    now = datetime.now(KST)
    title = "1인가구 전월세 안심계약 도움서비스"
    if not all(x in contents for x in (district+"]",title.replace(" ",""),"이용대상","무료","독립가구예정인자포함")):
        raise SourceError("신청처 또는 이용대상 확인 필요")
    day = now.date().isoformat()
    status = "확인 불가"
    if day > "2026-12-31":
        status = "기간 종료"
    elif day < "2026-01-01":
        status = "접수 예정"
    elif any(s in contents or s in text for s in ("접수마감","예산소진으로","접수가종료","모집마감")):
        status = "조기 마감·예산 소진"
    elif day < "2026-12-31" and form.next_step and "이용안내동의하기" in contents:
        status = "접수 중"
    rules = [("single","eq","yes"),("locationIntent","eq","yes")]
    p = dict(profile,locationIntent=profile.get("locationIntent") or ("yes" if profile.get("resident") in ("yes","planned") else None))
    return dict(policyId="seoul-contract:2026:"+bid,originalId=bid,round="2026년 · "+district,
        name=title,agency="서울특별시 1인가구지원과",scope="서울시",regions=[district],type="주거·주거비",
        benefit="무료 전월세 계약상담 및 집보기 동행",method="선택한 자치구에 사전 신청 후 전화 또는 대면 상담",
        start="2026-01-01",end="2026-12-31",status=status,sourceUrl=PORTAL,detailUrl=PORTAL,
        applyUrl=url,homepage=None,updatedAt=None,fetchedAt=now.isoformat(),statusCheckedAt=now.isoformat(),
        statusEvidence="선택 지역의 신청 절차에서 이용 동의 및 다음 단계 버튼 확인" if status=="접수 중" else status,
        evidence=[PORTAL,ANNUAL,url], findings=evaluate({"rules":rules,"detailUrl":url},p))

