"""
MovieBox Arabic Cloud Addon for Stremio
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests
import hashlib
import hmac
import base64
import time
import random
import string
from urllib.parse import urlparse, parse_qs, quote

MAIN_URL = "https://api3.aoneroom.com"

# مفاتيح التشفير الرسمية (المستخرجة والمترجمة من كود كوتلن)
SECRET_KEY_DEFAULT = base64.b64decode("NzZpUmwwN3MweFNOOWpxbUVXQXQ3OUVCSlp1bElRSXNWNjRGWnIyTw==")

MANIFEST = {
    "id": "org.abdullah.moviebox.addon",
    "version": "1.2.0",
    "name": "MovieBox Arabic Addon",
    "description": "إضافة موفيبوكس السحابية للأفلام والمسلسلات العالمية - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"]
}

def generate_device_id():
    return ''.join(random.choices(string.hexdigests, k=32)).lower()

DEVICE_ID = generate_device_id()

def md5_hex(data_bytes):
    return hashlib.md5(data_bytes).hexdigest()

def generate_x_client_token():
    timestamp = str(int(time.time() * 1000))
    reversed_ts = timestamp[::-1]
    hash_ts = md5_hex(reversed_ts.encode('utf-8'))
    return f"{timestamp},{hash_ts}"

def build_canonical_string(method, accept, content_type, url, body, timestamp):
    parsed_url = urlparse(url)
    path = parsed_url.path or ""
    
    query_params = parse_qs(parsed_url.query)
    if query_params:
        sorted_keys = sorted(query_params.keys())
        query_parts = []
        for key in sorted_keys:
            for val in query_params[key]:
                query_parts.append(f"{key}={val}")
        query_str = "&".join(query_parts)
        canonical_url = f"{path}?{query_str}"
    else:
        canonical_url = path

    body_bytes = body.encode('utf-8') if body else b""
    if body_bytes:
        # قص حقل الحماية إذا تجاوز الحجم الأقصى لضمان مطابقة الـ MD5 كما في كود كوتلن
        trimmed_bytes = body_bytes[:102400] if len(body_bytes) > 102400 else body_bytes
        body_hash = md5_hex(trimmed_bytes)
    else:
        body_hash = ""

    body_length = str(len(body_bytes)) if body_bytes else ""
    return f"{method.upper()}\n{accept or ''}\n{content_type or ''}\n{body_length}\n{timestamp}\n{body_hash}\n{canonical_url}"

def generate_x_tr_signature(method, accept, content_type, url, body=None):
    timestamp = str(int(time.time() * 1000))
    canonical = build_canonical_string(method, accept, content_type, url, body, timestamp)
    
    signature_hmac = hmac.new(SECRET_KEY_DEFAULT, canonical.encode('utf-8'), hashlib.md5).digest()
    signature_b64 = base64.b64encode(signature_hmac).decode('utf-8')
    return f"{timestamp}|2|{signature_b64}"

def get_base_headers(method, url, body=None, accept="application/json", content_type="application/json"):
    return {
        "user-agent": "com.community.mbox.in/50020042 (Linux; U; Android 16; en_IN; sdk_gphone64_x86_64; Build/BP22.250325.006; Cronet/133.0.6876.3)",
        "accept": accept,
        "content-type": content_type,
        "connection": "keep-alive",
        "x-client-token": generate_x_client_token(),
        "x-tr-signature": generate_x_tr_signature(method, accept, content_type, url, body),
        "x-client-info": json.dumps({
            "package_name": "com.community.mbox.in",
            "version_name": "3.0.03.0529.03",
            "version_code": 50020042,
            "os": "android",
            "os_version": "16",
            "device_id": DEVICE_ID,
            "install_store": "ps",
            "gaid": "d7578036d13336cc",
            "brand": "google",
            "model": "Pixel 8",
            "system_language": "en",
            "net": "NETWORK_WIFI",
            "region": "IN",
            "timezone": "Asia/Calcutta",
            "sp_code": ""
        }, separators=(',', ':')),
        "x-client-status": "0"
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. الرد بالـ Manifest الخاص بـ Stremio
        if self.path == "/api" or self.path == "/api/" or self.path == "/api/manifest.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

        # 2. ممر جلب فك التشفير وروابط البث لـ Stremio
        if "/api/stream/" in self.path:
            clean_path = self.path.replace("/api/stream/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            if len(parts) >= 2:
                media_type = parts[0]  
                stremio_id = parts[1]  
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"streams": []}).encode("utf-8"))
                return

            id_parts = stremio_id.split(":")
            imdb_id = id_parts[0]
            season = int(id_parts[1]) if len(id_parts) > 1 else 1
            episode = int(id_parts[2]) if len(id_parts) > 2 else 1

            # جلب تفاصيل العنوان الأساسي من قاعدة بيانات TMDB المفتوحة
            tmdb_url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key=d131017ccc6e5462a81c9304d21476de&external_source=imdb_id"
            title_query = ""
            try:
                tmdb_resp = requests.get(tmdb_url, timeout=8).json()
                results_key = 'tv_results' if media_type == 'series' else 'movie_results'
                if results_key in tmdb_resp and len(tmdb_resp[results_key]) > 0:
                    title_query = tmdb_resp[results_key][0].get('title') or tmdb_resp[results_key][0].get('name') or ""
            except:
                pass

            streams_result = {"streams": []}
            
            if title_query:
                # خطوة (أ): البحث النصي للحصول على الـ subjectId للمادة
                search_url = f"{MAIN_URL}/wefeed-mobile-bff/subject-api/search/v2"
                search_body = json.dumps({"page": 1, "perPage": 10, "keyword": title_query}, separators=(',', ':'))
                search_headers = get_base_headers('POST', search_url, search_body, content_type="application/json; charset=utf-8")
                
                try:
                    search_res = requests.post(search_url, headers=search_headers, data=search_body, timeout=10).json()
                    subject_ids = []
                    if search_res and "data" in search_res and "results" in search_res["data"]:
                        target_type = 1 if media_type == 'movie' else 2
                        for group in search_res["data"]["results"]:
                            if "subjects" in group:
                                for sub in group["subjects"]:
                                    if sub.get("subjectType") == target_type:
                                        sid = sub.get("subjectId")
                                        if sid: subject_ids.append(str(sid))
                    
                    # خطوة (ب): المرور على معرفات المواد وجلب روابط الـ streams الرسمية مع تمرير الـ token والكوكيز
                    for s_id in subject_ids[:2]:
                        play_url = f"{MAIN_URL}/wefeed-mobile-bff/subject-api/play-info?subjectId={s_id}&se={season}&ep={episode}"
                        play_headers = get_base_headers('GET', play_url)
                        
                        play_res = requests.get(play_url, headers=play_headers, timeout=10).json()
                        if play_res and "data" in play_res and "streams" in play_res["data"]:
                            for stream in play_res["data"]["streams"]:
                                if stream.get("url"):
                                    quality = stream.get("resolutions") or stream.get("quality") or "Auto"
                                    sign_cookie = stream.get("signCookie")
                                    
                                    # إعداد الهيدرز وتمرير كوكيز التوقيع المرفقة لكل جودة لمنع توقف الرابط
                                    stream_headers = {"Referer": MAIN_URL}
                                    if sign_cookie:
                                        stream_headers["Cookie"] = sign_cookie
                                        
                                    streams_result["streams"].append({
                                        "name": f"MovieBox {quality}",
                                        "title": f"🎬 سحابي مستقل ومحدث\n🍿 دقة العرض: {quality}\n⛓️‍💥 الحماية المحدثة",
                                        "url": stream.get("url"),
                                        "behaviorHints": {
                                            "proxyHeaders": {
                                                "request": stream_headers
                                            }
                                        }
                                    })
                except Exception as e:
                    print(f"API Processing Error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
