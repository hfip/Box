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

# البروكسي الخاص بك على كلود فلير لتأمين الاتصال وتفادي حظر السيرفرات السحابية
PROXY_BASE = "https://mbox-proxy.h-fip.workers.dev/"

# الروابط والممرات الخلفية السرية لشبكة H5
CATALOG_URL = PROXY_BASE + "h5-api.aoneroom.com/wefeed-h5api-bff/home?host=moviebox.ph"
PLAY_BASE_URL = PROXY_BASE + "h5-api.aoneroom.com/wefeed-h5api-bff/subject/play"

# توليفة الهيدرز الذهبية لمحاكاة التطبيق الرسمي كلياً
H5_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Referer": "https://moviebox.ph/",
    "Origin": "https://moviebox.ph",
    "X-Client-Type": "h5",
    "Accept": "application/json"
}

# تعريف الإضافة مع تفعيل ممرات الكتالوج (Catalogs) للتصفح المباشر
MANIFEST = {
    "id": "org.abdullah.moviebox.catalogs",
    "version": "2.0.0",
    "name": "MovieBox Arabic Catalogs",
    "description": "إضافة موفيبوكس السحابية للأقسام والبث المباشر المفتوح - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["catalog", "stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["mb"],  # بادئة خاصة بالمعرفات الداخلية لموفيبوكس لتجنب تعارض البحث
    "catalogs": [
        {
            "id": "mb_movies_trending",
            "type": "movie",
            "name": "🎬 MovieBox | أفلام تريند"
        },
        {
            "id": "mb_series_trending",
            "type": "series",
            "name": "📺 MovieBox | مسلسلات تريند"
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

        # 2. ممر جلب الأقسام وعرضها في واجهة Stremio (Catalog Handler)
        if "/api/catalog/" in self.path:
            clean_path = self.path.replace("/api/catalog/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            # تحديد نوع القسم المطلوب (أفلام أم مسلسلات)
            catalog_type = parts[0] if len(parts) > 0 else "movie"
            catalog_id = parts[1] if len(parts) > 1 else ""
            
            metas = []
            
            try:
                # جلب الـ JSON الصافي للأقسام مباشرة من الممر الخلفي
                resp = requests.get(CATALOG_URL, headers=H5_HEADERS, timeout=10).json()
                cards = resp.get("data", {}).get("cards", [])
                
                for card in cards:
                    # تصفية المحتوى بناءً على النوع (أفلام أو مسلسلات تريند)
                    card_title = str(card.get("title", "")).lower()
                    items = card.get("content", {}).get("items", [])
                    
                    # التحقق من مطابقة القسم للطلب الحالي
                    is_movie_req = (catalog_type == "movie" and "movie" in card_title)
                    is_series_req = (catalog_type == "series" and ("tv" in card_title or "series" in card_title))
                    
                    if is_movie_req or is_series_req or not catalog_id:
                        for item in items:
                            subject_id = item.get("subjectId")
                            title = item.get("title")
                            cover = item.get("cover")
                            detail_path = item.get("detailPath", "")
                            
                            if subject_id and title:
                                # صياغة المعرف الداخلي الذكي ليمرر الـ subjectId والـ detailPath معاً
                                combined_id = f"mb:{subject_id}:{quote(detail_path)}"
                                metas.append({
                                    "id": combined_id,
                                    "type": catalog_type,
                                    "name": title,
                                    "poster": cover,
                                    "description": f"فيلم/مسلسل حصري متوفر على شبكة MovieBox للهندسة العكسية. معرف المادة: {subject_id}"
                                })
            except Exception as e:
                print(f"Catalog fetch error: {e}")

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
            
            if len(parts) >= 2:
                media_type = parts[0]
                combined_id = parts[1]
            else:
                combined_id = ""

            streams_result = {"streams": []}

            # معالجة المعرفات القادمة من الأقسام المخصصة للإضافة (mb)
            if combined_id.startswith("mb:"):
                id_parts = combined_id.split(":")
                subject_id = id_parts[1] if len(id_parts) > 1 else ""
                detail_path = id_parts[2] if len(id_parts) > 2 else ""
                
                # إعداد بارامترات ممر الـ Play السري
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
                                "title": f"🎬 البث الذكي المباشر من ممر الأقسام\n🚀 دقة العرض المستقرة: {quality_label}\n✨ تطوير عبدالله @Abdullu.X",
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
                    print(f"Stream generation error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
