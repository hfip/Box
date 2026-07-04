"""
MovieBox Arabic Cloud Addon for Stremio
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests

# السيرفر الوسيط المحدث لمعالجة وفك تشفير الروابط بعيداً عن الحظر
CINESCRAPE_BASE = "https://cinescrape.com" 

# الـ Manifest الرسمي للإضافة داخل Stremio بحقوقك الكاملة
MANIFEST = {
    "id": "org.abdullah.moviebox.addon",
    "version": "1.1.0",
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
        if self.path == "/api" or self.path == "/api/" or self.path == "/api/manifest.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

        # 2. استقبال طلبات الـ Stream وفك التشفير وجلب المصادر
        if "/api/stream/" in self.path:
            clean_path = self.path.replace("/api/stream/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            if len(parts) >= 2:
                media_type = parts[0]  # movie أو series
                stremio_id = parts[1]  # معرف الـ IMDB الكامل (مثال: tt1234567)
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"streams": []}).encode("utf-8"))
                return

            # تحليل وتفكيك المعرف للمسلسلات والأفلام
            id_parts = stremio_id.split(":")
            imdb_id = id_parts[0]
            season = id_parts[1] if len(id_parts) > 1 else "1"
            episode = id_parts[2] if len(id_parts) > 2 else "1"

            # بناء ممر الطلب الذكي والبديل بناءً على نوع المحتوى لتفادي الحظر النصي
            if media_type == "series":
                target_url = f"{CINESCRAPE_BASE}/stream/tv/{imdb_id}:{season}:{episode}"
            else:
                target_url = f"{CINESCRAPE_BASE}/stream/movie/{imdb_id}"

            streams_result = {"streams": []}

            try:
                # طلب روابط البث المصفاة من السيرفر الوسيط المستقر
                response = requests.get(target_url, timeout=12)
                if response.status_code == 200:
                    data = response.json()
                    if "streams" in data and data["streams"]:
                        for stream in data["streams"]:
                            stream_url = stream.get("url", "")
                            
                            # تطبيق الفلتر الذكي: تخطي وحجب نطاق البث المسبب للحظر والشاشة السوداء كما فعل المطور
                            if "bcdnxw.hakunaymatata.com" in stream_url:
                                continue
                                
                            # استخراج تفاصيل الجودة والصيغة لبناء واجهة بث نظيفة
                            title_text = stream.get("title", stream.get("description", "Auto"))
                            quality = "1080p"
                            if "2160" in title_text or "4k" in title_text.lower():
                                quality = "4K 👑"
                            elif "720" in title_text:
                                quality = "720p"
                            elif "480" in title_text:
                                quality = "480p"

                            # إضافة الروابط الصافية والبديلة الشغالة إلى قائمة Stremio
                            streams_result["streams"].append({
                                "name": f"🎥 MovieBox | {quality}",
                                "title": f"🎬 سحابي مستقل ومحدث\n🍿 السيرفر البديل المستقر\n💾 الجودة المتاحة: {title_text}",
                                "url": stream_url,
                                "behaviorHints": stream.get("behaviorHints", {})
                            })
            except Exception as e:
                print(f"Fetch Error: {e}")

            # إرسال قائمة الروابط المصفاة والجاهزة إلى مشغل Stremio مباشرة
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
