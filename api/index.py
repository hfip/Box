"""
MovieBox Arabic Cloud Addon for Stremio
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests
import re
from urllib.parse import quote

# رابط البروكسي الخاص بك على كلود فلير لتخطي حظر السيرفر السحابي
PROXY_BASE = "https://mbox-proxy.h-fip.workers.dev/"

MANIFEST = {
    "id": "org.abdullah.moviebox.addon",
    "version": "1.4.0",
    "name": "MovieBox Arabic Addon",
    "description": "إضافة موفيبوكس السحابية للأفلام والمسلسلات العالمية - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"]
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. الرد بالـ Manifest لتثبيت الإضافة في Stremio
        if self.path in ["/api", "/api/", "/api/manifest.json"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

        # 2. استقبال طلبات الـ Stream من Stremio وفك التشفير بالخلطة الجديدة عبر البروكسي
        if "/api/stream/" in self.path:
            clean_path = self.path.replace("/api/stream/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            if len(parts) >= 2:
                media_type = parts[0]  # movie أو series
                stremio_id = parts[1]  # معرف IMDB
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

            streams_result = {"streams": []}

            try:
                # خطوة (أ): البحث في صفحات الويب لموفيبوكس من خلال البروكسي الخاص بك لتفادي الحظر
                target_search_url = f"moviebox.ph/web/searchResult?keyword={quote(imdb_id)}"
                search_url = PROXY_BASE + target_search_url
                
                search_resp = requests.get(search_url, timeout=15)
                
                # استخراج بيانات الـ NUXT المحدثة الخاصة بالموقع مباشرة
                match = re.search(r'<script[^>]+id="__NUXT_DATA__"[^>]*>(.*?)</script>', search_resp.text, re.DOTALL)
                
                if match:
                    nuxt_data = json.loads(match.group(1))
                    subject_id = None
                    detail_path = None
                    
                    # الفحص الذكي لاستخراج المعرف والـ Slug للمادة
                    for item in nuxt_data:
                        if isinstance(item, dict) and "subjectId" in item and "detailPath" in item:
                            subject_id = item.get("subjectId")
                            detail_path = item.get("detailPath")
                            break
                    
                    # خطوة (ب): إذا عثرنا على معرف المادة، نقوم بسحب الروابط فوراً عبر ممر الـ H5 المفتوح من خلال البروكسي
                    if subject_id and detail_path:
                        domains = ["h5-api.aoneroom.com", "moviebox.ph"]
                        streams_found = []
                        
                        for domain in domains:
                            target_play_url = f"{domain}/wefeed-h5api-bff/subject/play?subjectId={subject_id}&se={season}&ep={episode}&detailPath={quote(detail_path)}"
                            play_url = PROXY_BASE + target_play_url
                            
                            try:
                                play_resp = requests.get(play_url, timeout=12).json()
                                play_data = play_resp.get("data", {}) or {}
                                if "streams" in play_data and play_data["streams"]:
                                    streams_found = play_data["streams"]
                                    break # اقطع التكرار بمجرد جلب الروابط الحية بنجاح
                            except:
                                continue
                        
                        # line (ج): تنسيق الروابط وعرضها في واجهة Stremio
                        for s in streams_found:
                            stream_url = s.get("url")
                            if stream_url:
                                res = s.get("resolutions", "Auto")
                                quality_label = f"{res}p" if "p" not in str(res) else res
                                
                                streams_result["streams"].append({
                                    "name": f"🍿 MovieBox | {quality_label}",
                                    "title": f"🎬 البث السحابي الذكي المفتوح (عبر البروكسي)\n🚀 الجودة المستقرة: {quality_label}\n✨ تطوير عبدالله @Abdullu.X",
                                    "url": stream_url,
                                    "behaviorHints": {
                                        "proxyHeaders": {
                                            "request": {
                                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                                "Referer": "https://moviebox.ph/"
                                            }
                                        }
                                    }
                                })
                                
            except Exception as e:
                print(f"Proxy Cloud Scrape Error: {e}")

            # تسليم قائمة الروابط الصافية إلى تطبيق المشغل
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
