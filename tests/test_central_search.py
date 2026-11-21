import json
import unittest
from unittest.mock import patch
from policy import central_search as cs

class CentralSummaryTests(unittest.TestCase):
    def setUp(self):
        cs.sources._cache.clear()
        self.html="<h2>청년 전세임대 입주자 모집</h2><b>공급기관</b><span>LH</span><b>대상지역</b><p>서울특별시 동작구</p><b>공급호수</b><b>임대기간</b><span>2년</span>"
    def test_regional_notice_without_key(self):
        with patch.dict("os.environ",{},clear=True),patch.object(cs.sources,"fetch",side_effect=lambda u:"?pblancId=19631" if u==cs.INDEX else self.html):
            _,result=cs.search("동작구")
            self.assertEqual(result["myhomeCount"],1)
            self.assertIn("기본 요약",result["pending"][0]["reason"])
            self.assertEqual(cs.search("관악구")[1]["myhomeCount"],0)

    def test_summary_only(self):
        row=dict(sourceUrl=cs.DETAIL+"1234",facts=["임대기간 · 2년"])
        answer=json.dumps({"candidates":[{"content":{"parts":[{"text":'{"1234":[0]}'}]}}]})
        with patch.dict("os.environ",{"GEMINI_API_KEY":"test"},clear=True),patch.object(cs.sources,"fetch",return_value=answer) as api:
            self.assertEqual(cs.summarize([row])[0]["1234"],row["facts"][0])
            self.assertIn("gemini-3.5-flash:",api.call_args.args[0])
            self.assertNotIn("tools",json.loads(api.call_args.kwargs["body"]))
            api.side_effect=cs.sources.SourceError("Gemini HTTP 404")
            self.assertEqual(cs.summarize([row])[0],{})

    def test_official_failure(self):
        with patch.object(cs.sources,"fetch",side_effect=cs.sources.SourceError("오류")):
            with self.assertRaises(cs.sources.SourceError):cs.search("관악구")
