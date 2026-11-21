from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlsplit, parse_qs

from policy import sources
from policy.notices import KST

BASE = "https://housing.seoul.go.kr/site/main/lh/publicLease/list"
INDEX = BASE + "?" + urlencode({"cnpCdNm":"서울특별시"})

class Board(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = None
        self.cell = None
        self.link = ""
        self.rows = []
        self.pages = set()

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.cells, self.link = [], ""
        elif tag == "td" and self.cells is not None:
            self.cell = []
        elif tag == "a":
            href = urljoin(BASE, dict(attrs).get("href") or "")
            try:
                url = urlsplit(href)
            except ValueError:
                return
            if url.scheme == "https" and url.netloc == "apply.lh.or.kr" and self.cell is not None:
                self.link = href
            if url.path == urlsplit(BASE).path and url.netloc == "housing.seoul.go.kr":
                page = parse_qs(url.query).get("cp",[""])[0]
                if page.isdigit() and 1 < int(page) <= 100:
                    self.pages.add(int(page))

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.cells.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.cells is not None:
            if len(self.cells) == 8:
                self.rows.append((self.cells,self.link))
            self.cells = None

def listings():
    today = datetime.now(KST).date().isoformat()
    todo, done, cards = {1}, set(), {}
    errors = 0
    while todo:
        n = min(todo)
        todo.remove(n)
        done.add(n)
        page = Board()
        try:
            html = sources.fetch(INDEX + "&cp=" + str(n))
            page.feed(html)
            if not page.rows and "검색 결과가 없습니다" not in html:
                raise sources.SourceError("LH 공고 목록 형식 확인 필요")
        except sources.SourceError:
            if n == 1:
                raise
            errors += 1
            continue
        todo.update(page.pages - done)
        for cells, link in page.rows:
            _, kind, name, region, posted, end, status, _ = cells
            if "서울" not in region or status not in ("공고중","접수중","접수예정","공고 중","접수 중"):
                continue
            if end and len(end)==10 and end.replace(".","-") < today:
                continue
            cards[(name,posted)] = dict(name=name,sourceUrl=link or INDEX,
                linkLabel="LH 공식 공고" if link else "서울주거포털 공고 목록",
                reason=f"{region} · {kind} · {status} · 마감일 {end}. 공급 위치와 세부 자격은 공고에서 확인해 주세요.")
    return [],dict(pending=list(cards.values()),detailErrors=errors)
