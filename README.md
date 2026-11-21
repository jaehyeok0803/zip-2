# 24.zip 주거지원 정책 조회

## Vercel 배포

ZIP을 풀어 `index.html`, `api/`, `policy/`, `vercel.json`이 같은 폴더에 오도록 저장소에 올립니다. Vercel 프로젝트의 Root Directory로 그 폴더를 지정합니다. Framework Preset은 Other입니다. 배포 설정은 `node build.mjs`로 정적 파일을 `dist`로 복사합니다. API는 Python 표준 라이브러리로 실행합니다. 환경변수를 Production 또는 테스트할 Preview 환경에 저장한 뒤 재배포합니다. HTML을 더블클릭해서 여는 경우 API는 실행되지 않습니다. 로컬에서는 프로젝트 루트에서 `vercel dev`를 사용합니다.

| Vercel 환경변수 | 값과 발급처 |
|---|---|
| SEOUL_API_KEY | 서울 열린데이터광장 인증키. 기존에 등록한 이름을 재사용합니다. |
| SEOUL_WELFARE_LIST_SERVICE | 선택 사항. 기본값은 welfareServiceList입니다. |
| SEOUL_WELFARE_DETAIL_SERVICE | 선택 사항. 기본값은 welfareServiceDe입니다. |
| SEOUL_WELFARE_ID_FIELD | 원본 서비스 ID 필드가 servId/SERV_ID/serviceId와 다른 경우 공식 응답에 기재된 키를 지정합니다. |
| CENTRAL_WELFARE_API_KEY | 선택 사항. 중앙부처 복지서비스 API 인증키를 등록하면 해당 목록도 조회합니다. |

## 조회 범위

서울시·자치구 목록과 상세 자료를 서비스 ID로 연결해 공공임대 입주자 모집, 주거비와 청년 생활지원금 후보를 찾습니다. 월세·이사비·보증료·대출이자 등 주거비 부담을 줄이는 사업과 청년 생활비·수당·자립정착금이 대상입니다. LH 서울 공공임대와 마이홈 입주자 공고도 조회해 공식 안내로 연결합니다. 서울주거포털의 청년 임차보증금 이자지원도 조회합니다. 중앙부처 API는 별도 키가 있는 경우 목록 정보를 기준으로 선별합니다.

입력한 자치구와 공식 자료에서 해석할 수 있는 나이·소득·무주택 조건을 대조합니다. 결과 카드에 공식 상세 및 신청 주소가 제공되면 표시합니다. 복잡한 자격과 현재 접수 여부는 공식 안내에서 확인합니다.

## 확인

프로젝트 루트에서 `python -m unittest discover -s tests`로 테스트하고 `node build.mjs`로 정적 화면을 빌드합니다.
