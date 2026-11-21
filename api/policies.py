from http.server import BaseHTTPRequestHandler
import json
from policy.service import lookup,validate

class handler(BaseHTTPRequestHandler):
    def reply(self,code,body):
        data = json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","private, no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            if self.headers.get_content_type()!="application/json":
                return self.reply(415,{"error":"JSON 요청이 필요합니다."})
            size = int(self.headers.get("Content-Length","0"))
            if not 0<size<=8192:
                return self.reply(413,{"error":"요청 크기를 확인해 주세요."})
            data = json.loads(self.rfile.read(size))
            if not isinstance(data,dict):
                raise ValueError()
            profile = validate(data.get("profile"))
            only = data.get("recheckId")
            if only is not None and (not isinstance(only,str) or not 1<=len(only)<=200):
                raise ValueError()
        except (TypeError,ValueError):
            return self.reply(400,{"error":"입력 범위와 단위를 확인해 주세요."})
        try:
            result = lookup(profile,only)
            self.reply(503 if result["state"]=="failed" else 200,result)
        except Exception:
            self.reply(503,{"error":"정책 조회를 완료하지 못했습니다."})

    def do_GET(self):
        self.reply(405,{"error":"POST를 사용해 주세요."})

