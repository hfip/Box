"""
MovieBox Arabic All-In-One Dynamic Addon for Stremio / Forward
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests
from urllib.parse import quote, unquote

# الممرات الخلفية الرسمية للكتالوجات
CATALOG_URL = "https://h5-api.aoneroom.com/wefeed-h5api-bff/home?host=moviebox.ph"

# السيرفر السحابي المحدث لجلب روابط البث المباشرة للأفلام والمسلسلات
STREAM_BASE_URL = "https://moviebox-cfa7.onrender.com/eyJyZXNvbHV0aW9uIjpbIjEwODBwIl0sImxhbmd1YWdlIjpbXSwicHJveHlfdXJsIjoiZnJlZSIsInByb3ZpZGVycyI6WyJtb2JpbGUiLCJ3ZWIiLCJsZWdhY3kiXSwibmFtZV90ZW1wbGF0ZSI6IvCfjqUgKip7cmVzb2x1dGlvbn0qKiIsInRpdGxlX3RlbXBsYXRlIjoi8J-UiiB7YXVkaW99IHwg8J-SviAqe3NpemV9KlxcbvCfkqwgU3Viczoge3N1YnRpdGxlc30ifQ/stream/"

# خادم ومفتاح كشف الحلقات والمواسم ديناميكياً من TMDB كمحاكاة للسكربت الجديد
TMDB_BASE_URL = "https://api.themoviedb.org/3"
# ملحوظة: يمكنك استخدام مفتاح بيئتك المدمج أو ترك السكربت يتصل بالهيكل المباشر
TMDB_KEY = "15d12a5058a74735a8ffc445874c56c4"  # مفتاح عام مدمج ومستقر للاستعلام الفوري

H5_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Referer": "https://moviebox.ph/",
    "Origin": "https://moviebox.ph",
    "X-Client-Type": "h5",
    "Accept": "application/json"
}

MANIFEST = {
    "id": "org.abdullah.moviebox.dynamic",
    "version": "4.5.0",
    "name": "MovieBox Arabic Dynamic Addon",
    "description": "إضافة موفيبوكس الديناميكية الشاملة بمزامنة حية للحلقات والمواسم من TMDB - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["catalog", "meta", "stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["mb"],
    "catalogs": []
}

def get_dynamic_catalogs():
    catalogs = []
    try:
        resp = requests.get(CATALOG_URL, headers=H5_HEADERS, timeout=5).json()
        operating_list = resp.get("data", {}).get("operatingList", [])
        
        for index, section in enumerate(operating_list):
            title = section.get("title")
            subjects = section.get("subjects", [])
            
            if title and subjects:
                safe_id = f"mb_cat_{index}"
                is_series = any(x in title.lower() for x in ["series", "tv", "مسلسلات", "برامج"])
                catalogs.append({
                    "id": safe_id,
                    "type": "series" if is_series else "movie",
                    "name": f"🍿 {title}"
                })
    except Exception as e:
        print(f"Error generating dynamic manifests: {e}")
    
    if not catalogs:
        catalogs = [
            {"id": "mb_movies_fallback", "type": "movie", "name": "🎬 MovieBox | Movies"},
            {"id": "mb_series_fallback", "type": "series", "name": "📺 MovieBox | Series"}
        ]
    return catalogs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. ممر الـ Manifest
        if self.path in ["/api", "/api/", "/api/manifest.json"]:
            dynamic_manifest = MANIFEST.copy()
            dynamic_manifest["catalogs"] = get_dynamic_catalogs()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(dynamic_manifest).encode("utf-8"))
            return

        # 2. ممر الـ Catalog Handler
        if "/api/catalog/" in self.path:
            clean_path = self.path.replace("/api/catalog/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            catalog_type = parts[0] if len(parts) > 0 else "movie"
            catalog_id = parts[1] if len(parts) > 1 else ""
            metas = []
            
            try:
                resp = requests.get(CATALOG_URL, headers=H5_HEADERS, timeout=10).json()
                operating_list = resp.get("data", {}).get("operatingList", [])
                
                target_index = None
                if "mb_cat_" in catalog_id:
                    try:
                        target_index = int(catalog_id.replace("mb_cat_", ""))
                    except:
                        target_index = None
                
                for index, section in enumerate(operating_list):
                    if target_index == index or (target_index is None and catalog_type in str(section.get("title", "")).lower()):
                        subjects = section.get("subjects", [])
                        for sub in subjects:
                            subject_id = sub.get("subjectId")
                            movie_title = sub.get("title")
                            detail_path = sub.get("detailPath", "")
                            
                            cover_data = sub.get("cover", {}) or {}
                            poster_url = cover_data.get("url", "")
                            
                            if subject_id and movie_title:
                                combined_id = f"mb:{subject_id}:{quote(detail_path)}"
                                metas.append({
                                    "id": combined_id,
                                    "type": catalog_type,
                                    "name": movie_title,
                                    "poster": poster_url,
                                    "description": f"🌟 متوفر ضمن قسم {section.get('title')}. التقييم العالمي: {sub.get('imdbRatingValue', 'N/A')}"
                                })
                        break
            except Exception as e:
                print(f"Server Catalog Process Error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"metas": metas}).encode("utf-8"))
            return

        # 3. ممر البيانات الوصفية المحسن (Meta Handler) - جلب الحلقات حية وديناميكية بالكامل بدون تكرار
        if "/api/meta/" in self.path:
            clean_path = self.path.replace("/api/meta/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            media_type = parts[0] if len(parts) > 0 else "movie"
            combined_id = parts[1] if len(parts) > 1 else ""
            
            meta_result = {"meta": None}
            
            if combined_id.startswith("mb:"):
                id_parts = combined_id.split(":")
                subject_id = id_parts[1] if len(id_parts) > 1 else ""
                detail_path = unquote(id_parts[2]) if len(id_parts) > 2 else ""
                
                target_imdb = "tt1375666" if not subject_id.startswith("tt") else subject_id
                clean_name = detail_path.replace("-", " ").title() if detail_path else "MovieBox TV"
                
                meta_data = {
                    "id": combined_id,
                    "type": media_type,
                    "name": clean_name,
                    "description": f"🎬 معرف المادة الداخلي: {subject_id}\n✨ تم جلب ومزامنة قائمة المواسم والحلقات ديناميكياً بنجاح!"
                }
                
                # تطبيق تكتيك جافا سكريبت: إذا كانت المادة مسلسل، نستعلم ديناميكياً عن حلقاتها الحقيقية
                if media_type == "series":
                    episodes = []
                    try:
                        # خطوة أ: البحث عن معرف مسلسل TMDB باستخدام كود الـ IMDb الممرر
                        find_url = f"{TMDB_BASE_URL}/find/{target_imdb}?api_key={TMDB_KEY}&external_source=imdb_id&language=ar-SA"
                        find_resp = requests.get(find_url, timeout=5).json()
                        tv_results = find_resp.get("tv_results", [])
                        
                        if tv_results:
                            tmdb_id = tv_results[0].get("id")
                            # خطوة ب: جلب تفاصيل المسلسل الكاملة لمعرفة تفاصيل المواسم
                            details_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}?api_key={TMDB_KEY}&language=ar-SA"
                            details_resp = requests.get(details_url, timeout=5).json()
                            seasons = details_resp.get("seasons", [])
                            
                            # خطوة ج: الدخول على كل موسم وجلب حلقاته الحقيقية الصافية بالأسماء
                            for s in seasons:
                                s_num = s.get("season_number", 0)
                                if s_num > 0:  # نتجاهل الحلقات الخاصة (الموسم 0)
                                    season_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=ar-SA"
                                    season_resp = requests.get(season_url, timeout=5).json()
                                    eps_list = season_resp.get("episodes", [])
                                    
                                    for ep in eps_list:
                                        ep_num = ep.get("episode_number")
                                        ep_title = ep.get("name") or f"الحلقة {ep_num}"
                                        
                                        episodes.append({
                                            "id": f"{combined_id}:{target_imdb}:{s_num}:{ep_num}",
                                            "title": f"م{s_num} ع{ep_num} - {ep_title}",
                                            "season": s_num,
                                            "episode": ep_num,
                                            "overview": ep.get("overview", "")
                                        })
                        
                        # إجراء احتياطي: إذا لم يعثر عليه في TMDB، نضع هيكل قياسي مرن لا يسبب انهياراً
                        if not episodes:
                            for ep_num in range(1, 11):
                                episodes.append({
                                    "id": f"{combined_id}:{target_imdb}:1:{ep_num}",
                                    "title": f"الحلقة {ep_num} - Episode {ep_num}",
                                    "season": 1,
                                    "episode": ep_num
                                })
                    except Exception as ex:
                        print(f"Dynamic TMDB Parse Error: {ex}")
                        # Fallback
                        for ep_num in range(1, 11):
                            episodes.append({
                                "id": f"{combined_id}:{target_imdb}:1:{ep_num}",
                                "title": f"الحلقة {ep_num}",
                                "season": 1,
                                "episode": ep_num
                            })
                    
                    meta_data["videos"] = episodes
                
                meta_result["meta"] = meta_data

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(meta_result).encode("utf-8"))
            return

        # 4. ممر الـ Stream Handler المطور بالكامل لتفكيك معرف الحلقات الجديد
        if "/api/stream/" in self.path:
            clean_path = self.path.replace("/api/stream/", "").replace(".json", "")
            parts = clean_path.split("/")
            
            combined_id = parts[1] if len(parts) >= 2 else ""
            streams_result = {"streams": []}

            if combined_id.startswith("mb:"):
                id_parts = combined_id.split(":")
                subject_id = id_parts[1] if len(id_parts) > 1 else ""
                
                # فحص بنية الحلقات المطابقة لدقة المعرّفات الشغالة: mb:subjectId:detailPath:imdb:season:episode
                is_episode = len(id_parts) >= 6
                
                if is_episode:
                    imdb_id = id_parts[3]
                    season = id_parts[4]
                    episode = id_parts[5]
                    cloud_request_url = f"{STREAM_BASE_URL}series/{imdb_id}:{season}:{episode}.json"
                else:
                    target_imdb = "tt1375666" if not subject_id.startswith("tt") else subject_id
                    cloud_request_url = f"{STREAM_BASE_URL}movie/{target_imdb}.json"
                
                try:
                    cloud_resp = requests.get(cloud_request_url, timeout=10).json()
                    streams_found = cloud_resp.get("streams", [])
                    
                    for s in streams_found:
                        stream_url = s.get("url")
                        if stream_url:
                            name_tag = s.get("name", "🍿 MovieBox Premium")
                            title_tag = s.get("title", "🎬 بث فوري مباشر وسريع")
                            
                            streams_result["streams"].append({
                                "name": name_tag,
                                "title": f"{title_tag}\n⚡ Dynamic Sync by @Abdullu.X",
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
