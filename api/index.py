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

# مفاتيح التشفير المستخرجة من الكود (Double Base64 Decode)[span_0](start_span)[span_0](end_span)
KEY_B64_DEFAULT = "NzZpUmwwN3MweFNOOWpxbUVXQXQ3OUVCSlp1bElRSXNWNjRGWnIyTw=="
SECRET_KEY = base64.b64decode(base64.b64decode(KEY_B64_DEFAULT).decode('utf-8'))[span_1](start_span)[span_1](end_span)

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
    return hashlib.md5(data_bytes).hexdigest()[span_2](start_span)[span_2](end_span)

def generate_x_client_token(timestamp_str):
    reversed_ts = timestamp_str[::-1][span_3](start_span)[span_3](end_span)
    hash_ts = md5_hex(reversed_ts.encode('utf-8'))[span_4](start_span)[span_4](end_span)
    return f"{timestamp_str},{hash_ts}[span_5](start_span)"[span_5](end_span)

def build_canonical_string(method, accept, content_type, url, body, timestamp_str):
    parsed_url = urlparse(url)[span_6](start_span)[span_6](end_span)
    path = parsed_url.path[span_7](start_span)[span_7](end_span)
    
    query_params = parse_qs(parsed_url.query)[span_8](start_span)[span_8](end_span)
    sorted_keys = sorted(query_params.keys())[span_9](start_span)[span_9](end_span)
    
    query_parts = []
    for key in sorted_keys:
        for val in query_params[key]:[span_10](start_span)[span_10](end_span)
            query_parts.append(f"{key}={val}")[span_11](start_span)[span_11](end_span)
    query_str = "&".join(query_parts)[span_12](start_span)[span_12](end_span)
    
    canonical_url = f"{path}?{query_str}" if query_str else path[span_13](start_span)[span_13](end_span)
    
    body_hash = ""
    body_length = ""
    if body:
        body_bytes = body.encode('utf-8')[span_14](start_span)[span_14](end_span)
        body_hash = md5_hex(body_bytes)[span_15](start_span)[span_15](end_span)
        body_length = str(len(body_bytes))[span_16](start_span)[span_16](end_span)
        
    return f"{method.upper()}\n{accept}\n{content_type}\n{body_length}\n{timestamp_str}\n{body_hash}\n{canonical_url}[span_17](start_span)"[span_17](end_span)

def generate_x_tr_signature(method, accept, content_type, url, body, timestamp_str):
    canonical = build_canonical_string(method, accept, content_type, url, body, timestamp_str)[span_18](start_span)[span_18](end_span)
    signature_hmac = hmac.new(SECRET_KEY, canonical.encode('utf-8'), hashlib.md5).digest()[span_19](start_span)[span_19](end_span)
    signature_b64 = base64.b64encode(signature_hmac).decode('utf-8')[span_20](start_span)[span_20](end_span)
    return f"{timestamp_str}|2|{signature_b64}[span_21](start_span)"[span_21](end_span)

def make_moviebox_request(method, url, body=None):
    timestamp_str = str(int(time.time() * 1000))[span_22](start_span)[span_22](end_span)
    accept = 'application/json[span_23](start_span)'[span_23](end_span)
    content_type = 'application/json[span_24](start_span)'[span_24](end_span)
    
    headers = HEADERS_TEMPLATE.copy()[span_25](start_span)[span_25](end_span)
    headers['Accept'] = accept[span_26](start_span)[span_26](end_span)
    headers['Content-Type'] = content_type[span_27](start_span)[span_27](end_span)
    headers['x-client-token'] = generate_x_client_token(timestamp_str)[span_28](start_span)[span_28](end_span)
    headers['x-tr-signature'] = generate_x_tr_signature(method, accept, content_type, url, body, timestamp_str)[span_29](start_span)[span_29](end_span)
    
    try:
        if method.upper() == 'POST':
            resp = requests.post(url, headers=headers, data=body, timeout=15)[span_30](start_span)[span_30](end_span)
        else:
            resp = requests.get(url, headers=headers, timeout=15)[span_31](start_span)[span_31](end_span)
        if resp.status_code == 200:[span_32](start_span)[span_32](end_span)
            return resp.json()[span_33](start_span)[span_33](end_span)
    except Exception as e:
        print(f"Request Error: {e}")[span_34](start_span)[span_34](end_span)
    return None[span_35](start_span)[span_35](end_span)

class MovieBoxHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ممر فحص ماني والـ Manifest الرئيسي للإضافة
        if self.path == "/api" or self.path == "/api/" or self.path == "/api/manifest.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

        # ممر فك التشفير وجلب الروابط لـ Stremio
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
                search_url = f"{API_BASE}/wefeed-mobile-bff/subject-api/search/v2[span_36](start_span)"[span_36](end_span)
                search_body = json.dumps({"page": 1, "perPage": 5, "keyword": title_query}, separators=(',', ':'))[span_37](start_span)[span_37](end_span)
                search_res = make_moviebox_request('POST', search_url, search_body)[span_38](start_span)[span_38](end_span)
                
                subject_id = None
                if search_res and "data" in search_res and "results" in search_res["data"]:[span_39](start_span)[span_39](end_span)
                    target_type = 1 if media_type == 'movie' else 2[span_40](start_span)[span_40](end_span)
                    for group in search_res["data"]["results"]:[span_41](start_span)[span_41](end_span)
                        if "subjects" in group:[span_42](start_span)[span_42](end_span)
                            for sub in group["subjects"]:[span_43](start_span)[span_43](end_span)
                                if sub.get("subjectType") == target_type:[span_44](start_span)[span_44](end_span)
                                    subject_id = sub.get("subjectId")[span_45](start_span)[span_45](end_span)
                                    break
                        if subject_id: break

                if subject_id:
                    play_url = f"{API_BASE}/wefeed-mobile-bff/subject-api/play-info?subjectId={subject_id}&se={season}&ep={episode}[span_46](start_span)"[span_46](end_span)
                    play_res = make_moviebox_request('GET', play_url)[span_47](start_span)[span_47](end_span)
                    
                    if play_res and "data" in play_res and "streams" in play_res["data"]:[span_48](start_span)[span_48](end_span)
                        for stream in play_res["data"]["streams"]:[span_49](start_span)[span_49](end_span)
                            if stream.get("url"):[span_50](start_span)[span_50](end_span)
                                quality = stream.get("resolutions") or stream.get("quality") or "Auto[span_51](start_span)"[span_51](end_span)
                                streams_result["streams"].append({
                                    "name": f"MovieBox {quality}",
                                    "title": f"🎬 سحابي مستقل وآمن\n🍿 دقة العرض المتوفرة: {quality}",
                                    "url": stream.get("url"),
                                    "headers": {
                                        "Referer": API_BASE,
                                        "User-Agent": HEADERS_TEMPLATE['User-Agent'],
                                        **({"Cookie": stream.get("signCookie")} if stream.get("signCookie") else {})
                                    }
                                })[span_52](start_span)[span_52](end_span)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

# السطر الجوهري لتصدير المتغير وتخطي خطأ فيرسيل بنجاح
handler = MovieBoxHandler
