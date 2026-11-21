import unittest
from unittest.mock import patch
from policy import sources
from policy.central_search import from_myhome,parse_notice,DETAIL

class SourceRecovery(unittest.TestCase):
    def test_seoul_defaults(self):
        with patch.dict("os.environ",{"SEOUL_API_KEY":"test"},clear=True),patch.object(sources,"seoul_table",side_effect=[[{"SERV_ID":"a"}],[{"SERV_ID":"a","info":"detail"}]]) as table:
            records,warning=sources.seoul()
            self.assertEqual([c.args[0] for c in table.call_args_list],["welfareServiceList","welfareServiceDe"])
            self.assertEqual(records["a"]["detail"][0]["info"],"detail")
            self.assertFalse(warning)

    def test_seoul_retains_list_on_detail_failure(self):
        with patch.dict("os.environ",{"SEOUL_API_KEY":"test"},clear=True),patch.object(sources,"seoul_table",side_effect=[[{"SERV_ID":"a"}],sources.SourceError("상세 오류")]):
            records,warning=sources.seoul()
            self.assertEqual(records["a"]["list"],[{"SERV_ID":"a"}])
            self.assertFalse(records["a"]["detail"])
            self.assertTrue(warning)

    def test_myhome_desktop_recovery(self):
        page="<h2>청년 전세임대 입주자 모집</h2><p>공급기관: LH</p><p>대상지역: 서울</p><p>공급호수</p><p>임대기간: 2년</p>"
        with patch.object(sources,"fetch",side_effect=[sources.SourceError("마이홈 HTTP 503"),page]):
            row=from_myhome(DETAIL+"19631",parse_notice)
            self.assertIn("www.myhome.go.kr",row["sourceUrl"])
            self.assertIn("임대기간 · 2년",row["facts"])
