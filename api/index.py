"""
MovieBox Arabic Catalog & Stream Addon for Stremio
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests
from urllib.parse import quote

# الممرات الرسمية والخلفية المباشرة والمكشوفة لشبكة H5
CATALOG_URL = "https://h5-api.aoneroom.com/wefeed-h5api-bff/home?host=moviebox.ph"
PLAY_BASE_URL = "https://h5-api.aoneroom.com/wefeed-h5api-bff/subject/play"

# توليفة الهيدرز الرسمية المعتمدة في الـ Pyto لتخطي أي حظر عميل
H5_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Referer": "https://moviebox.ph/",
    "Origin": "https://moviebox.ph",
    "X-Client-Type": "h5",
    "Accept": "application/json"
}

# مصفوفة التعريف للـ Manifest مع التصنيفات المطابقة لـ داتا السيرفر الحية
MANIFEST = {
    "id": "org.abdullah.moviebox.catalogs",
    "version": "2.2.0",
    "name": "MovieBox Arabic Catalogs",
    "description": "إضافة موفيبوكس السحابية للأقسام والبث المباشر المفتوح - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["catalog", "stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["mb"],
    "catalogs": [
        {
            "id": "mb_movies_popular",
            "type": "movie",
            "name": "🎬 MovieBox | أفلام شائعة"
        },
        {
            "id": "mb_series_popular",
            "type": "series",
            "name": "📺 MovieBox | مسلسلات شائعة"
        }
    ]
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. الرد بالـ Manifest لتثبيت الإضافة
        if self.path in ["/api", "/api/", "/api/manifest.json"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(MANIFEST).encode("utf-8"))
            return

        # 2. ممر جلب الأقسام واستخراج البوسترات (Catalog Handler)
        if "/api/catalog/" in self.path:
            clean_path = self.path.replace("/api/catalog/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            catalog_type = parts[0] if len(parts) > 0 else "movie"
            metas = []
            
            try:
                # طلب قائمة التصنيفات مباشرة ومطابقتها مع اختبار الجوال الموثوق
                resp = requests.get(CATALOG_URL, headers=H5_HEADERS, timeout=10).json()
                operating_list = resp.get("data", {}).get("operatingList", [])
                
                for section in operating_list:
                    title = str(section.get("title", "")).lower()
                    subjects = section.get("subjects", [])
                    
                    # الفرز الذكي والمطابق لأسماء خوادم الكتالوج
                    is_movie_section = (catalog_type == "movie" and "popular movie" in title)
                    is_series_section = (catalog_type == "series" and "popular series" in title)
                    
                    if is_movie_section or is_series_section:
                        for sub in subjects:
                            subject_id = sub.get("subjectId")
                            movie_title = sub.get("title")
                            detail_path = sub.get("detailPath", "")
                            
                            # استخراج غلاف البوستر الصافي بدقة
                            cover_data = sub.get("cover", {}) or {}
                            poster_url = cover_data.get("url", "")
                            
                            if subject_id and movie_title:
                                combined_id = f"mb:{subject_id}:{quote(detail_path)}"
                                metas.append({
                                    "id": combined_id,
                                    "type": catalog_type,
                                    "name": movie_title,
                                    "poster": poster_url,
                                    "description": f"🍿 مادة ميديا حصرية متوفرة عبر إضافة موفيبوكس. التقييم: {sub.get('imdbRatingValue', 'N/A')}"
                                })
            except Exception as e:
                print(f"Server Catalog Process Error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"metas": metas}).encode("utf-8"))
            return

        # 3. ممر جلب روابط البث المباشر وتشغيل المادة فوراً (Stream Handler)
        if "/api/stream/" in self.path:
            clean_path = self.path.replace("/api/stream/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            combined_id = parts[1] if len(parts) >= 2 else ""
            streams_result = {"streams": []}

            if combined_id.startswith("mb:"):
                id_parts = combined_id.split(":")
                subject_id = id_parts[1] if len(id_parts) > 1 else ""
                detail_path = id_parts[2] if len(id_parts) > 2 else ""
                
                # توجيه طلب التشغيل مباشرة بالهيدرز الكاملة
                play_url = f"{PLAY_BASE_URL}?subjectId={subject_id}&se=0&ep=0&detailPath={detail_path}"
                
                try:
                    play_resp = requests.get(play_url, headers=H5_HEADERS, timeout=10).json()
                    play_data = play_resp.get("data", {}) or {}
                    streams_found = play_data.get("streams", [])
                    
                    for s in streams_found:
                        stream_url = s.get("url")
                        if stream_url:
                            res = s.get("resolutions", "Auto")
                            quality_label = f"{res}p" if "p" not in str(res) else res
                            
                            streams_result["streams"].append({
                                "name": f"🍿 MovieBox | {quality_label}",
                                "title": f"🎬 تشغيل فوري مباشر ومستقر من الكتالوج\n✨ تطوير عبدالله @Abdullu.X",
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
                    print(f"Server Stream Process Error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
