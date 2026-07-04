"""
MovieBox All-in-One Cloud Addon for Stremio
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
from urllib.parse import urlparse, parse_qs

API_BASE = "https://api.inmoviebox.com"

# مفاتيح التشفير المستخرجة من الكود (Double Base64 Decode)
KEY_B64_DEFAULT = "NzZpUmwwN3MweFNOOWpxbUVXQXQ3OUVCSlp1bElRSXNWNjRGWnIyTw=="
SECRET_KEY = base64.b64decode(base64.b64decode(KEY_B64_DEFAULT).decode('utf-8'))

HEADERS_TEMPLATE = {
    'User-Agent': 'com.community.mbox.in/50020042 (Linux; U; Android 16; en_IN; sdk_gphone64_x86_64; Build/BP22.250325.006; Cronet/133.0.6876.3)',
    'Connection': 'keep-alive',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'x-client-info': '{"package_name":"com.community.mbox.in","version_name":"3.0.03.0529.03","version_code":50020042,"os":"android","os_version":"16","device_id":"da2b99c821e6ea023e4be55b54d5f7d8","install_store":"ps","gaid":"d7578036d13336cc","brand":"google","model":"sdk_gphone64_x86_64","system_language":"en","net":"NETWORK_WIFI","region":"IN","timezone":"Asia/Calcutta","sp_code":""}',
    'x-client-status': '0'
}

MANIFEST = {
    "id": "org.abdullah.moviebox.addon",
    "version": "1.0.0",
    "name": "MovieBox Arabic Addon",
    "description": "إضافة موفيبوكس السحابية للأفلام والمسلسلات العالمية - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"]
}

def md5_hex(data_bytes):
    return hashlib.md5(data_bytes).hexdigest()

def generate_x_client_token(timestamp_str):
    reversed_ts = timestamp_str[::-1]
    hash_ts = md5_hex(reversed_ts.encode('utf-8'))
    return f"{timestamp_str},{hash_ts}"

def build_canonical_string(method, accept, content_type, url, body, timestamp_str):
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    query_params = parse_qs(parsed_url.query)
    sorted_keys = sorted(query_params.keys())
    
    query_parts = []
    for key in sorted_keys:
        for val in query_params[key]:
            query_parts.append(f"{key}={val}")
    query_str = "&".join(query_parts)
    
    canonical_url = f"{path}?{query_str}" if query_str else path
    
    body_hash = ""
    body_length = ""
    if body:
        body_bytes = body.encode('utf-8')
        body_hash = md5_hex(body_bytes)
        body_length = str(len(body_bytes))
        
    return f"{method.upper()}\n{accept}\n{content_type}\n{body_length}\n{timestamp_str}\n{body_hash}\n{canonical_url}"

def generate_x_tr_signature(method, accept, content_type, url, body, timestamp_str):
    canonical = build_canonical_string(method, accept, content_type, url, body, timestamp_str)
    signature_hmac = hmac.new(SECRET_KEY, canonical.encode('utf-8'), hashlib.md5).digest()
    signature_b64 = base64.b64encode(signature_hmac).decode('utf-8')
    return f"{timestamp_str}|2|{signature_b64}"

def make_moviebox_request(method, url, body=None):
    timestamp_str = str(int(time.time() * 1000))
    accept = 'application/json'
    content_type = 'application/json'
    
    headers = HEADERS_TEMPLATE.copy()
    headers['Accept'] = accept
    headers['Content-Type'] = content_type
    headers['x-client-token'] = generate_x_client_token(timestamp_str)
    headers['x-tr-signature'] = generate_x_tr_signature(method, accept, content_type, url, body, timestamp_str)
    
    try:
        if method.upper() == 'POST':
            resp = requests.post(url, headers=headers, data=body, timeout=15)
        else:
            resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Request Error: {e}")
    return None

# التسمية المباشرة للكلاس لتخطي متطلبات المنصة الافتراضية بنجاح
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api" or self.path == "/api/" or self.path == "/api/manifest.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

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
            season = int(id_parts[1]) if len(id_parts) > 1 else 0
            episode = int(id_parts[2]) if len(id_parts) > 2 else 0

            tmdb_url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key=d131017ccc6e5462a81c9304d21476de&external_source=imdb_id"
            title_query = ""
            try:
                tmdb_resp = requests.get(tmdb_url, timeout=10).json()
                results_key = 'tv_results' if media_type == 'series' else 'movie_results'
                if results_key in tmdb_resp and len(tmdb_resp[results_key]) > 0:
                    title_query = tmdb_resp[results_key][0].get('title') or tmdb_resp[results_key][0].get('name') or ""
            except:
                pass

            streams_result = {"streams": []}
            
            if title_query:
                search_url = f"{API_BASE}/wefeed-mobile-bff/subject-api/search/v2"
                search_body = json.dumps({"page": 1, "perPage": 5, "keyword": title_query}, separators=(',', ':'))
                search_res = make_moviebox_request('POST', search_url, search_body)
                
                subject_id = None
                if search_res and "data" in search_res and "results" in search_res["data"]:
                    target_type = 1 if media_type == 'movie' else 2
                    for group in search_res["data"]["results"]:
                        if "subjects" in group:
                            for sub in group["subjects"]:
                                if sub.get("subjectType") == target_type:
                                    subject_id = sub.get("subjectId")
                                    break
                        if subject_id: break

                if subject_id:
                    play_url = f"{API_BASE}/wefeed-mobile-bff/subject-api/play-info?subjectId={subject_id}&se={season}&ep={episode}"
                    play_res = make_moviebox_request('GET', play_url)
                    
                    if play_res and "data" in play_res and "streams" in play_res["data"]:
                        for stream in play_res["data"]["streams"]:
                            if stream.get("url"):
                                quality = stream.get("resolutions") or stream.get("quality") or "Auto"
                                streams_result["streams"].append({
                                    "name": f"MovieBox {quality}",
                                    "title": f"🎬 سحابي مستقل وآمن\n🍿 دقة العرض المتوفرة: {quality}",
                                    "url": stream.get("url"),
                                    "headers": {
                                        "Referer": API_BASE,
                                        "User-Agent": HEADERS_TEMPLATE['User-Agent'],
                                        **({"Cookie": stream.get("signCookie")} if stream.get("signCookie") else {})
                                    }
                                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
