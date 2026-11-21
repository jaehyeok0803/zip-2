"""Official catalogue adapters. Keys and upstream URLs never enter client errors."""
import json
import os
import re
import time
from threading import Lock
from urllib.error import HTTPError
from urllib.parse import urlencode, quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from xml.etree import ElementTree as ET

class SourceError(Exception):
    pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None

HOSTS = {"openapi.seoul.go.kr", "apis.data.go.kr", "generativelanguage.googleapis.com",
         "www.myhome.go.kr", "m.myhome.go.kr", "data.seoul.go.kr", "1in.seoul.go.kr", "youth.seoul.go.kr", "ydp1in.or.kr", "housing.seoul.go.kr", "www.sd.go.kr"}
def fetch(url, *, body=None, headers=None, timeout=5):
    u = urlsplit(url)
    official_seoul = u.scheme == "http" and u.hostname == "openapi.seoul.go.kr" and u.port == 8088
    secure = u.scheme == "https" and u.hostname in HOSTS and u.port in (None, 443)
    if not (secure or official_seoul) or u.username or u.password:
        raise SourceError("허용되지 않은 출처")
    request = Request(url, data=body, headers={"User-Agent":"24zip-policy/1.0", **(headers or {})})
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as res:
            data = res.read(10_000_001)
            if len(data) > 10_000_000:
                raise SourceError("응답 크기 초과")
            return data.decode(res.headers.get_content_charset() or "utf-8-sig")
    except HTTPError as e:
        if u.hostname == "generativelanguage.googleapis.com":
            try:
                payload = json.loads(e.read(16384))
            except (ValueError, OSError):
                payload = {}
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            error = error if isinstance(error, dict) else {}
            status = error.get("status", "")
            label = " " + status if isinstance(status,str) and status in (
                "NOT_FOUND","INVALID_ARGUMENT","FAILED_PRECONDITION","PERMISSION_DENIED",
                "UNAUTHENTICATED","RESOURCE_EXHAUSTED","INTERNAL","UNAVAILABLE") else ""
            message = str(error.get("message","")).lower()
            hint = {400:"요청 형식 또는 프로젝트 이용 조건 확인",401:"인증키 확인",
                    403:"프로젝트 권한 및 키 제한 확인",404:"설정 모델의 접근 권한과 지원 여부 확인",
                    429:"프로젝트 검색 할당량 확인",500:"잠시 후 재시도",503:"잠시 후 재시도"}.get(e.code,"공급자 응답 확인 필요")
            if e.code==404 and "no longer available to new users" in message:
                hint = "신규 사용자에게 제공되지 않는 모델"
            elif e.code==400 and "api key not valid" in message:
                hint = "Google에서 인증키를 유효하지 않은 값으로 판정"
            raise SourceError(f"Gemini HTTP {e.code}{label} · {hint}") from None
        if u.hostname in ("m.myhome.go.kr","www.myhome.go.kr"):
            raise SourceError(f"마이홈 HTTP {e.code}") from None
        raise SourceError({401:"인증 실패",403:"접근 거부",429:"호출 한도 초과"}.get(e.code,"공급자 HTTP 오류")) from None
    except (OSError, ValueError):
        raise SourceError("연결 또는 응답 형식 오류") from None

_cache = {}
_lock = Lock()
def cached(key, reader):
    with _lock:
        hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < 300:
        return hit[1]
    value = reader()
    with _lock:
        _cache[key] = (time.monotonic(), value)
    return value

def seoul_table(service, key):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", service):
        raise SourceError("영문 서비스명 설정 확인 필요")
    rows = []
    for start in range(1, 50001, 500):
        url = f"http://openapi.seoul.go.kr:8088/{quote(key,safe='')}/json/{service}/{start}/{start+499}/"
        payload = json.loads(fetch(url))
        table = payload.get(service, {})
        code = (payload.get("RESULT") or table.get("RESULT") or {}).get("CODE")
        if code == "INFO-200" and start == 1:
            return []
        if code != "INFO-000":
            raise SourceError("서울 API 인증·서비스명·호출 한도 확인 필요")
        batch = table.get("row")
        if not isinstance(batch, list) or not batch:
            raise SourceError("목록 누락")
        rows.extend(batch)
        if len(rows) == int(table["list_total_count"]):
            return rows
        if len(batch) != 500:
            raise SourceError("페이지 일부 누락")
    raise SourceError("조회 범위 초과")

def seoul():
    key = os.getenv("SEOUL_API_KEY")
    list_service = os.getenv("SEOUL_WELFARE_LIST_SERVICE") or "welfareServiceList"
    detail_service = os.getenv("SEOUL_WELFARE_DETAIL_SERVICE") or "welfareServiceDe"
    if not key:
        raise SourceError("미연결")
    rows = seoul_table(list_service,key)
    if not rows:
        return {}, ""
    warning = ""
    id_field = os.getenv("SEOUL_WELFARE_ID_FIELD")
    def by_id(rows):
        result = {}
        for row in rows:
            field = id_field or next((k for k in row if k.lower().replace("_","") in ("servid","serviceid")), None)
            if not field or not row.get(field):
                raise SourceError("원본 서비스ID 필드 확인 필요")
            result.setdefault(str(row[field]), []).append(row)
        return result
    listing = by_id(rows)
    details = {}
    try:
        details = by_id(seoul_table(detail_service,key))
        if listing.keys()-details.keys():
            warning = "일부 정책 상세 미확인"
    except (SourceError,ValueError,KeyError,TypeError):
        warning = "목록 조회 완료 · 상세 응답 확인 불가"
    return {k:{"list":v,"detail":details.get(k,[])} for k,v in listing.items()}, warning


def national_xml(operation, **params):
    key = os.getenv("CENTRAL_WELFARE_API_KEY")
    if not key:
        raise SourceError("미연결")
    url = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/" + operation
    root = ET.fromstring(fetch(url + "?" + urlencode(dict(serviceKey=key, **params))))
    code = root.findtext(".//resultCode")
    if code not in ("0","00","000","0000"):
        raise SourceError("중앙부처 API 인증·응답 코드 확인 필요")
    return root

def national():
    result = {}
    for page in range(1,101):
        root = national_xml("NationalWelfarelistV001",callTp="L",pageNo=page,numOfRows=100,srchKeyCode="003")
        total = int(root.findtext(".//totalCount"))
        entries = root.findall(".//servList")
        for item in entries:
            identifier = item.findtext("servId")
            if not identifier or identifier in result:
                raise SourceError("목록 식별자 누락·중복")
            result[identifier] = {child.tag:child.text for child in item}
        if len(result) == total:
            return result
        if not entries:
            break
    raise SourceError("전체 목록 조회 미완료")

def national_detail(identifier):
    root = national_xml("NationalWelfaredetailedV001",callTp="D",servId=identifier)
    if root.findtext(".//servId") != identifier:
        raise SourceError("상세 식별자 불일치")
    return ET.tostring(root, encoding="unicode")

