"""
Stremio Addon Frontend Interface
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests

# الـ Manifest الرسمي لتعريف إضافتك داخل تطبيق Stremio
MANIFEST = {
    "id": "org.abdullah.moviebox.addon",
    "version": "1.0.0",
    "name": "MovieBox Arabic Addon",
    "description": "إضافة موفيبوكس السحابية للأفلام والمسلسلات العالمية - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico", # أيقونة موفيبوكس الرسمية
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"] # البادئة الرسمية لمعرفات IMDB / TMDB
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. عند فتح الرابط الرئيسي للإضافة أو الـ Manifest
        if self.path == "/api/addon" or self.path == "/api/addon/manifest.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

        # 2. عندما يطلب Stremio روابط التشغيل (Stream Request)
        # النمط القادم من Stremio يكون: /api/addon/stream/movie/tt1234567.json
        if "/api/addon/stream/" in self.path:
            try:
                # تنظيف المسار واستخراج نوع المحتوى والمعرف
                clean_path = self.path.replace("/api/addon/stream/", "").replace(".json", "")
                parts = clean_path.split("/")
                media_type = parts[0] # movie أو series
                stremio_id = parts[1] # tt1234567 أو tt1234567:1:1

                # تحويل الطلب داخلياً إلى المحرك الخلفي (api/index.py) الذي رفعناه سابقاً
                # نقوم بطلب الرابط محلياً من نفس الدومين لتوليد التواقيع وسحب مخرجات موفيبوكس
                backend_url = f"https://box-ochre.vercel.app/api/resolve/{media_type}/{stremio_id}"
                
                response = requests.get(backend_url, timeout=12)
                if response.status_code == 200:
                    streams_data = response.json()
                else:
                    streams_data = {"streams": []}
            except Exception as e:
                streams_data = {"streams": []}

            # إرسال روابط البث المشفرة والمستخرجة مباشرة إلى مشغل Stremio
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_data).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
