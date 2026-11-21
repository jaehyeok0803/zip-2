import json
import unittest
from datetime import datetime,timedelta
from unittest.mock import patch
from policy import notices,service,sources,contract,explain
from policy.notices import KST

class PolicyTests(unittest.TestCase):
    def test_zero_and_missing(self):
        p=service.validate(dict(district="동작구",monthly=0,personalIncome=None))
        self.assertEqual(p["monthly"],0)
        self.assertNotIn("personalIncome",p)
        for bad in (True,-1,"0",float("inf")):
            with self.assertRaises(ValueError):service.validate(dict(district="동작구",monthly=bad))

    def test_eligibility(self):
        n=dict(detailUrl="source",rules=[("resident","eq","yes"),("householdIncome","le",3000)])
        f=notices.evaluate(n,dict(resident="planned",personalIncome=1000))
        self.assertEqual([x["status"] for x in f],["불충족","확인 필요"])

    def test_admission(self):
        n=dict(notices.NOTICE,closure=None,anchors=["회차 일치"],openPattern="접수 중",
               deadline="2026-11-30T18:00:00+09:00")
        text="회차 일치 접수 중"
        now=datetime(2026,11,21,tzinfo=KST)
        for at,t,want in [(now,text,"접수 중"),(now,text+" (모집마감)","조기 마감·예산 소진"),
            (datetime(2026,11,30,18,tzinfo=KST),text,"기간 종료"),
            (datetime(2026,1,1,tzinfo=KST),text,"접수 예정"),(now,"접수 중","확인 불가")]:
            self.assertEqual(notices.admission(n,t,at),want)

    def test_sources_and_region(self):
        rows = {"WLF1":{"list":[{"SERV_NM":"청년 월세 지원","SGG_NM":"동작구"}],"detail":[]}}
        with patch.object(sources,"cached",side_effect=lambda k,f:f()),patch.object(sources,"seoul",return_value=(rows,"")),patch.object(service,"listings",return_value=([],{})),patch.object(service,"search",return_value=([],{})),patch.object(service,"loan_review",return_value=([],{})),patch.dict("os.environ",{},clear=True):
            for district,count in (("동작구",1),("관악구",0)):
                result=service.lookup({"district":district})
                self.assertEqual(len(result["sources"][0]["cards"]),count)
                self.assertEqual({s["name"] for s in result["sources"]},{"서울시·자치구 복지서비스","서울주거포털","LH · 서울 공공임대 공고","중앙부처 · 마이홈 공식 공고"})

    def test_pagination(self):
        def get(url):
            start=int(url.split("/")[-3])
            rows=[{"id":i} for i in range(start,min(start+500,503))]
            return json.dumps({"svc":{"RESULT":{"CODE":"INFO-000"},"list_total_count":502,"row":rows}})
        with patch.object(sources,"fetch",side_effect=get):
            self.assertEqual(len(sources.seoul_table("svc","sample")),502)
        with patch.object(sources,"fetch",return_value='{"RESULT":{"CODE":"ERROR-300"}}'):
            with self.assertRaises(sources.SourceError):sources.seoul_table("svc","key")

    def test_gemini_validation(self):
        item=dict(policyId="test",findings=[dict(label="만 나이")])
        fallback="만 나이 조건을 충족해요."
        ans=dict(policyId="other",refs=["0"],explanation="지원금 99만원")
        response=json.dumps({"candidates":[{"content":{"parts":[{"text":json.dumps(ans)}]}}]})
        with patch.dict("os.environ",{"GEMINI_API_KEY":"test","GEMINI_MODEL":"test"}),patch.object(explain,"fetch",return_value=response):
            self.assertEqual(explain.explain(item)[0],fallback)

    def test_failures(self):
        with patch.dict("os.environ",{},clear=True),patch("policy.contract.fetch",side_effect=sources.SourceError("조회 실패")):
            self.assertEqual(service.lookup({"district":"동작구"})["state"],"failed")

