import unittest
from unittest.mock import patch
from policy.discovery import catalogue_cards
from policy import lh


class DynamicResults(unittest.TestCase):
    def test_housing_must_be_the_benefit(self):
        from policy.discovery import candidate, summarize
        def record(name, benefit, criteria):
            return {"list":[{"SERV_NM":name}],"detail":[{"SPRT_CN":benefit,"SLCT_CRIT_CN":criteria}]}
        records = {
            "jobs":record("서울 경력단절여성등 재취업 지원사업","구직활동지원금 월 30만원","주거복지사 자격증 소지자"),
            "food":record("식생활 지원","임대주택 입주자에게 밑반찬 제공","서울 거주"),
            "rent":record("위기가구 긴급지원","취업상담 및 월세 일부 지원","서울 거주"),
            "repair":record("기초생활수급자 집수리","도배 및 장판 교체","서울 거주"),
        }
        records.update({
            "hospital":record("청년 입원 생활비 지원","청년 생활비 지급","서울 거주"),
            "youth":record("서울 청년수당","월 50만원 지급","미취업 청년"),
            "fees":record("중개보수 및 이사비 지원","실비 지급","서울 거주"),
            "rental":record("청년 매입임대 입주자 모집","임대주택 공급","서울 거주"),
            "medical":record("임대주택 입주자 입원비 지원","병원비 지급","입주자"),
            "waiting":record("행복주택 예비입주자 추가 모집","신청 접수","서울 거주"),
            "kit":record("전입 청년 웰컴키트","생활용품 제공","서울 거주"),
        })
        self.assertEqual([k for k,v in records.items() if candidate(v)],["rent","youth","fees","rental","waiting"])
        self.assertEqual(summarize("seoul",records)["discovered"],5)
        self.assertEqual(len(catalogue_cards(records,{"district":"영등포구"})),5)

    def test_dynamic_region_conditions_and_links(self):
        def record(district, age):
            return {"list":[{"SERV_NM":"새 월세지원","SGG_NM":district}],
                    "detail":[{"SPRT_TRGT_CN":age,"APLY_URL":"javascript:bad"}]}
        data = {"WLF1":record("영등포구","만 19~39세 무주택 청년"),
                "WLF2":record("강남구",""),"WLF3":record("서울특별시","만 60~70세"),
                "WLF4":record("서울특별시","만 60~70세 또는 무주택 청년")}
        cards = catalogue_cards(data,{"district":"영등포구","age":28,"noHome":"yes"})
        self.assertEqual(len(cards),2)
        self.assertIn("나이 일치",cards[0]["reason"])
        self.assertIn("WLF1",cards[0]["sourceUrl"])
        self.assertFalse(cards[0]["applyUrl"])
        self.assertEqual(len(catalogue_cards(data,{"district":"영등포구"})),3)

    def test_lh_pagination_excludes_closed(self):
        def page(status, title):
            cells=["1","전세임대",title,"서울특별시","2026-01-01","2099-01-01",status,
                   '<a href="https://apply.lh.or.kr/notice">바로가기</a>']
            return "<tr>"+ "".join("<td>"+c+"</td>" for c in cells)+"</tr>"
        pages=[page("접수마감","마감 공고")+'<a href="?cp=2">2</a>',page("공고중","새 공고")]
        with patch.object(lh.sources,"fetch",side_effect=pages):
            _, result=lh.listings()
        self.assertEqual([r["name"] for r in result["pending"]],["새 공고"])
        self.assertEqual(result["pending"][0]["sourceUrl"],"https://apply.lh.or.kr/notice")
