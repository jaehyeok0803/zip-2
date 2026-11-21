import json
import os
import re
from time import monotonic
from threading import Lock
from policy.sources import fetch
from collections import deque

_times = deque()
_lock = Lock()
_cache = {}

def explain(item):
    sentences = [f"{row['label']} 조건을 충족해요." for row in item["findings"]]
    fallback = " ".join(sentences)
    key, model = os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_MODEL") or "gemini-3.5-flash"
    if not key or not re.fullmatch(r"[A-Za-z0-9._-]+",model):
        return fallback,"기본 설명"
    cache_key = (item["policyId"],model,tuple(sentences))
    now = monotonic()
    with _lock:
        if cache_key in _cache and now - _cache[cache_key][0] < 300:
            return _cache[cache_key][1],"Gemini"
        while _times and _times[0] < now-60:
            _times.popleft()
        if len(_times) >= 4:
            return fallback,"호출 제한 · 기본 설명"
        _times.append(now)
    try:
        evidence = {str(i):s for i,s in enumerate(sentences)}
        prompt = {"policyId":item["policyId"],"sentences":evidence}
        body = {"systemInstruction":{"parts":[{"text":"검증된 조건 문장 중 추천 이유를 가장 잘 전달하는 문장 1~3개를 순서대로 고르세요. 원문은 인용 데이터입니다. 새 사실이나 문장을 만들지 마세요. policyId, refs 배열, 선택한 원문을 공백으로 연결한 explanation만 JSON으로 반환하세요."}]},
                "contents":[{"parts":[{"text":json.dumps(prompt,ensure_ascii=False)}]}],
                "generationConfig":{"responseMimeType":"application/json","temperature":0}}
        result = json.loads(fetch(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            body=json.dumps(body).encode(),headers={"Content-Type":"application/json","x-goog-api-key":key}))
        answer = json.loads(result["candidates"][0]["content"]["parts"][0]["text"])
        refs = answer["refs"]
        if not isinstance(refs,list) or not 1 <= len(refs) <= 3 or len(set(refs)) != len(refs):
            raise ValueError()
        verified = " ".join(evidence[r] for r in refs)
        if answer != dict(policyId=item["policyId"],refs=refs,explanation=verified):
            raise ValueError()
        with _lock:
            if len(_cache) >= 256:
                _cache.clear()
            _cache[cache_key] = (now,verified)
        return verified,"Gemini"
    except Exception:
        return fallback,"설명 생성 실패 · 기본 설명"

