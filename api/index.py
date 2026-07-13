"""
MovieBox Arabic Stream-Only Cloud Addon for Stremio / Forward
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests

# السيرفر السحابي المباشر والمستقر لجلب روابط البث المباشرة
STREAM_BASE_URL = "https://moviebox-cfa7.onrender.com/eyJyZXNvbHV0aW9uIjpbIjEwODBwIl0sImxhbmd1YWdlIjpbXSwicHJveHlfdXJsIjoiZnJlZSIsInByb3ZpZGVycyI6WyJtb2JpbGUiLCJ3ZWIiLCJsZWdhY3kiXSwibmFtZV90ZW1wbGF0ZSI6IvCfjqUgKip7cmVzb2x1dGlvbn0qKiIsInRpdGxlX3RlbXBsYXRlIjoi8J-UiiB7YXVkaW99IHwg8J-SviAqe3NpemV9KlxcbvCfkqwgU3Viczoge3N1YnRpdGxlc30ifQ/stream/"

MANIFEST = {
    "id": "org.abdullah.moviebox.streams",
    "version": "5.1.0",
    "name": "MovieBox Premium Streams",
    "description": "مصادر بث سحابية مباشرة وسريعة تدعم جميع الأفلام والمسلسلات العالمية - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"],
    "behaviorHints": {
        "configurable": False,
        "configurationRequired": False
    }
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. ممر الـ Manifest الأساسي
        if self.path in ["/api", "/api/", "/api/manifest.json"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

        # 2. ممر البث المباشر (Stream Handler) - إصلاح التفكيك للأفلام والمسلسلات
        if "/api/stream/" in self.path:
            clean_path = self.path.replace("/api/stream/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            media_type = parts[0] if len(parts) > 0 else "movie"
            full_id = parts[1] if len(parts) > 1 else ""
            
            streams_result = {"streams": []}

            if full_id.startswith("tt"):
                id_parts = full_id.split(":")
                imdb_id = id_parts[0]
                
                # فحص دقيق: هل هو مسلسل ويحتوي على موسم وحلقة فعلياً؟
                is_episode = len(id_parts) >= 3 and media_type == "series"
                
                if is_episode:
                    season = id_parts[1]
                    episode = id_parts[2]
                    cloud_request_url = f"{STREAM_BASE_URL}series/{imdb_id}:{season}:{episode}.json"
                else:
                    # للأفلام الصافية أو المعرفات المفردة
                    cloud_request_url = f"{STREAM_BASE_URL}movie/{imdb_id}.json"
                
                try:
                    cloud_resp = requests.get(cloud_request_url, timeout=10).json()
                    streams_found = cloud_resp.get("streams", [])
                    
                    for s in streams_found:
                        stream_url = s.get("url")
                        if stream_url:
                            # جلب الأسماء والرموز المحددة من السيرفر الأصلي أو وضع وسوم بريميوم
                            name_tag = s.get("name") or "🍿 MovieBox Premium"
                            title_tag = s.get("title") or "🎬 بث فوري سحابي مباشر"
                            
                            # حقن هيدر ExoPlayer الخارق لفتح أقصى سرعة للبث
                            streams_result["streams"].append({
                                "name": name_tag,
                                "title": f"{title_tag}\n⚡ Cloud Route by @Abdullu.X",
                                "url": stream_url,
                                "behaviorHints": {
                                    "proxyHeaders": {
                                        "request": {
                                            "User-Agent": "ExoPlayer/2.18.1 (Linux; Android 11; Pixel 5) ExoPlayerLib/2.18.1"
                                        }
                                    }
                                }
                            })
                except Exception as e:
                    print(f"Cloud Stream Fetch Error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
