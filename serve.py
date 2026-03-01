# -*- coding: utf-8 -*-
"""
프로젝트 인덱스 로컬 서버
실행: python serve.py
접속: http://localhost:9999
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess, urllib.parse, os, json, re

ROOT = os.path.dirname(os.path.abspath(__file__))


def scan_project(folder_path):
    """폴더를 스캔하여 index.html 위치와 HTML 메타 정보를 추출합니다."""
    folder_path = os.path.normpath(folder_path)

    if not os.path.isdir(folder_path):
        return {'error': 'not_found'}

    folder_name = os.path.basename(folder_path)

    # index.html 탐색: 루트 → 서브폴더(1단계)
    index_path = None
    rel_preview = None
    is_sub = False

    root_idx = os.path.join(folder_path, 'index.html')
    if os.path.exists(root_idx):
        index_path = root_idx
        rel_preview = folder_name + '/index.html'
    else:
        try:
            for item in sorted(os.listdir(folder_path)):
                sub_idx = os.path.join(folder_path, item, 'index.html')
                if os.path.exists(sub_idx):
                    index_path = sub_idx
                    rel_preview = folder_name + '/' + item + '/index.html'
                    is_sub = True
                    break
        except Exception:
            pass

    result = {'preview': rel_preview, 'is_sub': is_sub,
              'title': None, 'desc': None, 'tags': []}

    if not index_path:
        return result

    # HTML 파싱으로 메타 정보 추출
    try:
        with open(index_path, encoding='utf-8', errors='replace') as f:
            html = f.read(12000)  # 앞 12KB 만 읽기

        # <title>
        m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
        if m:
            result['title'] = m.group(1).strip()

        # <meta name="description"> — 속성 순서 무관
        m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{4,})["\']', html, re.I)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']{4,})["\'][^>]+name=["\']description["\']', html, re.I)
        if m:
            result['desc'] = m.group(1).strip()

        # description 없으면 첫 번째 <p> 또는 <h1>/<h2> 텍스트로 대체
        if not result['desc']:
            for tag in ('h1', 'h2', 'p'):
                m = re.search(r'<' + tag + r'[^>]*>([^<]{8,})</' + tag + r'>', html, re.I)
                if m:
                    text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                    if len(text) >= 8:
                        result['desc'] = text[:120]
                        break

        # <meta name="keywords">
        m = re.search(r'<meta[^>]+name=["\']keywords["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']keywords["\']', html, re.I)
        if m:
            result['tags'] = [t.strip() for t in m.group(1).split(',') if t.strip()][:6]

        # 태그 없으면 폴더명 키워드로 자동 생성
        if not result['tags']:
            words = re.findall(r'[가-힣A-Za-z0-9]+', folder_name)
            result['tags'] = [w for w in words if len(w) >= 2][:5]

    except Exception:
        pass

    return result


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/open':
            params = urllib.parse.parse_qs(parsed.query)
            path = params.get('path', [''])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            if path and path != '__check__' and os.path.exists(path):
                subprocess.Popen(['explorer', os.path.normpath(path)])
            self.wfile.write(b'ok')
            return

        if parsed.path == '/scan':
            params = urllib.parse.parse_qs(parsed.query)
            path = params.get('path', [''])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            result = scan_project(path) if path else {'error': 'no_path'}
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return

        super().do_GET()

    def log_message(self, fmt, *args):
        pass  # 로그 숨김


PORT = 9999
os.chdir(ROOT)

print('=' * 45)
print('  Project Index Server')
print('  http://localhost:{}'.format(PORT))
print('  Stop: Ctrl+C')
print('=' * 45)

try:
    HTTPServer(('localhost', PORT), Handler).serve_forever()
except KeyboardInterrupt:
    print('Server stopped.')
    sys.exit(0)
