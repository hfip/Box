"""
MovieBox Arabic All-In-One Dynamic Addon for Stremio
Developed by: Abdullah
Telegram: @Abdullu.X
Year: 2026
"""

from http.server import BaseHTTPRequestHandler
import json
import requests
from urllib.parse import quote, unquote

# الممرات الخلفية الرسمية والمباشرة لشبكة H5 (الاتصال المباشر الموثوق من اختبار الجوال)
CATALOG_URL = "https://h5-api.aoneroom.com/wefeed-h5api-bff/home?host=moviebox.ph"
PLAY_BASE_URL = "https://h5-api.aoneroom.com/wefeed-h5api-bff/subject/play"
TOKEN_SOURCE_URL = "https://h5-api.aoneroom.com/wefeed-h5api-bff/app/get-latest-app-pkgs"

H5_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Referer": "https://netfilm.world/",
    "Origin": "https://netfilm.world",
    "X-Client-Info": json.dumps({"timezone": "Asia/Riyadh"}),
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# صياغة الـ Manifest الأساسي للإضافة
MANIFEST = {
    "id": "org.abdullah.moviebox.dynamic",
    "version": "4.0.0",
    "name": "MovieBox Arabic Dynamic Addon",
    "description": "إضافة موفيبوكس الديناميكية الشاملة لجميع الأقسام والروابط المباشرة - تطوير عبدالله @Abdullu.X",
    "logo": "https://themoviebox.org/favicon.ico",
    "resources": ["catalog", "meta", "stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["mb"],
    "catalogs": []  # يتم ملؤه ديناميكياً في خطوة الـ Manifest لتجنب كتابة الأقسام يدوياً
}


# دالة جلب توكن mb_token طازج من هيدر الاستجابة x-user لأي طلب على H5 API
def get_fresh_mb_token():
    try:
        resp = requests.get(
            TOKEN_SOURCE_URL,
            headers=H5_HEADERS,
            params={"app_name": "moviebox"},
            timeout=8
        )
        x_user_header = resp.headers.get("x-user")
        if not x_user_header:
            return None
        user_data = json.loads(x_user_header)
        return user_data.get("token")
    except Exception as e:
        print(f"Token Fetch Error: {e}")
        return None


# دالة مساعدة لجلب الأقسام حية من السيرفر وبناء قائمة الكتالوجات ديناميكياً
def get_dynamic_catalogs():
    catalogs = []
    try:
        resp = requests.get(CATALOG_URL, headers=H5_HEADERS, timeout=5).json()
        operating_list = resp.get("data", {}).get("operatingList", [])

        for index, section in enumerate(operating_list):
            title = section.get("title")
            subjects = section.get("subjects", [])

            # ننشئ كتالوج فقط إذا كان القسم يحتوي على مواد حقيقية لمنع الواجهات الفارغة
            if title and subjects:
                # توليد معرف فرعي آمن للقسم يعتمد على الترتيب والعنوان
                safe_id = f"mb_cat_{index}"
                catalogs.append({
                    "id": safe_id,
                    "type": "movie" if "movie" in title.lower() else "series",
                    "name": f"🍿 {title}"
                })
    except Exception as e:
        print(f"Error generating dynamic manifests: {e}")

    # إذا فشل الجلب لأي سبب، نضع كتالوجات احتياطية لضمان عدم انهيار الإضافة
    if not catalogs:
        catalogs = [
            {"id": "mb_movies_fallback", "type": "movie", "name": "🎬 MovieBox | Movies"},
            {"id": "mb_series_fallback", "type": "series", "name": "📺 MovieBox | Series"}
        ]
    return catalogs


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. ممر الـ Manifest (يولد الأقسام ديناميكياً عند تثبيت أو قراءة الإضافة)
        if self.path in ["/api", "/api/", "/api/manifest.json"]:
            dynamic_manifest = MANIFEST.copy()
            dynamic_manifest["catalogs"] = get_dynamic_catalogs()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(dynamic_manifest).encode("utf-8"))
            return

        # 2. ممر جلب داتا الأقسام والبوسترات بشكل ديناميكي (Catalog Handler)
        if "/api/catalog/" in self.path:
            clean_path = self.path.replace("/api/catalog/", "").replace(".json", "")
            parts = clean_path.split("/")

            catalog_type = parts[0] if len(parts) > 0 else "movie"
            catalog_id = parts[1] if len(parts) > 1 else ""
            metas = []

            try:
                # جلب الـ JSON الأصلي من السيرفر
                resp = requests.get(CATALOG_URL, headers=H5_HEADERS, timeout=10).json()
                operating_list = resp.get("data", {}).get("operatingList", [])

                # استخراج رقم الفهرس (Index) من معرف الكتالوج المطلوب
                target_index = None
                if "mb_cat_" in catalog_id:
                    try:
                        target_index = int(catalog_id.replace("mb_cat_", ""))
                    except:
                        target_index = None

                # جلب القسم المطابق للطلب وعرض محتوياته فوراً
                for index, section in enumerate(operating_list):
                    # التحقق: إما يطابق الفهرس المستخرج، أو يطابق النوع كإجراء احتياطي
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
                                    "description": f"🌟 فيلم/مسلسل متوفر ضمن قسم {section.get('title')}. التقييم العالمي: {sub.get('imdbRatingValue', 'N/A')}"
                                })
                        break  # خرج بعد العثور على القسم لضمان سرعة الاستجابة
            except Exception as e:
                print(f"Server Catalog Process Error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps({"metas": metas}).encode("utf-8"))
            return

        # 3. ممر معالجة البيانات الوصفية الفورية (Meta Handler) - لحل مشكلة الفراغ
        if "/api/meta/" in self.path:
            clean_path = self.path.replace("/api/meta/", "").replace(".json", "")
            parts = clean_path.split("/")

            media_type = parts[0] if len(parts) > 0 else "movie"
            combined_id = parts[1] if len(parts) > 1 else ""

            meta_result = {"meta": {}}

            if combined_id.startswith("mb:"):
                id_parts = combined_id.split(":")
                subject_id = id_parts[1] if len(id_parts) > 1 else ""
                detail_path = unquote(id_parts[2]) if len(id_parts) > 2 else ""

                # صياغة عنوان افتراضي نظيف مستخرج من مسار الفيلم للـ Stremio
                clean_name = detail_path.replace("-", " ").title() if detail_path else "MovieBox Media"

                meta_result["meta"] = {
                    "id": combined_id,
                    "type": media_type,
                    "name": clean_name,
                    "description": f"🎬 معرف المادة الداخلي: {subject_id}\n✨ تم توليد البيانات الوصفية وحل مشكلة العرض بنجاح. روابط البث جاهزة ومستقرة بالأسفل!"
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(meta_result).encode("utf-8"))
            return

        # 4. ممر جلب روابط البث وتشغيل الميديا مباشرة (Stream Handler)
        if "/api/stream/" in self.path:
            clean_path = self.path.replace("/api/stream/", "").replace(".json", "")
            parts = clean_path.split("/")

            combined_id = parts[1] if len(parts) >= 2 else ""
            streams_result = {"streams": []}

            if combined_id.startswith("mb:"):
                id_parts = combined_id.split(":")
                subject_id = id_parts[1] if len(id_parts) > 1 else ""
                detail_path = id_parts[2] if len(id_parts) > 2 else ""

                # جلب توكن طازج قبل كل طلب بث (التوكن قصير العمر ولازم يتجدد)
                fresh_token = get_fresh_mb_token()

                request_headers = dict(H5_HEADERS)
                if fresh_token:
                    request_headers["Cookie"] = f"mb_token={fresh_token}"

                params = {
                    "id": subject_id,
                    "se": 0,
                    "ep": 0,
                    "detailPath": detail_path,
                    "lang": "en"
                }

                try:
                    play_resp_raw = requests.get(
                        PLAY_BASE_URL,
                        headers=request_headers,
                        params=params,
                        timeout=10
                    )
                    play_resp = play_resp_raw.json()
                    play_data = play_resp.get("data", {}) or {}

                    streams_found = play_data.get("streams", [])
                    dash_found = play_data.get("dash", [])

                    # ===== وضع تشخيص مؤقت: احذفه بعد التأكد من نجاح الروابط =====
                    if not streams_found and not dash_found:
                        server_location = None
                        try:
                            geo_resp = requests.get("https://ipapi.co/json/", timeout=5).json()
                            server_location = {
                                "ip": geo_resp.get("ip"),
                                "country": geo_resp.get("country_name"),
                                "region": geo_resp.get("region"),
                                "city": geo_resp.get("city")
                            }
                        except Exception as geo_e:
                            server_location = {"error": str(geo_e)}

                        streams_result["debug"] = {
                            "token_fetched": bool(fresh_token),
                            "status_code": play_resp_raw.status_code,
                            "raw_response": play_resp,
                            "params_sent": params,
                            "vercel_server_location": server_location
                        }
                    # ================================================================

                    for s in streams_found:
                        stream_url = s.get("url")
                        if stream_url:
                            res = s.get("resolutions", "Auto")
                            quality_label = f"{res}p" if "p" not in str(res) else res

                            streams_result["streams"].append({
                                "name": f"🍿 MovieBox | {quality_label}",
                                "title": f"🎬 تشغيل فوري مستقر ومباشر من ممر الأقسام\n✨ تطوير عبدالله @Abdullu.X",
                                "url": stream_url,
                                "behaviorHints": {
                                    "proxyHeaders": {
                                        "request": {
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                            "Referer": "https://netfilm.world/"
                                        }
                                    }
                                }
                            })

                    for d in dash_found:
                        dash_url = d.get("url")
                        if dash_url:
                            streams_result["streams"].append({
                                "name": "🍿 MovieBox | 1080p [DASH]",
                                "title": f"🎬 جودة عالية DASH (HEVC)\n✨ تطوير عبدالله @Abdullu.X",
                                "url": dash_url,
                                "behaviorHints": {
                                    "proxyHeaders": {
                                        "request": {
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                            "Referer": "https://netfilm.world/"
                                        }
                                    }
                                }
                            })

                except Exception as e:
                    streams_result["debug"] = {"exception": str(e)}
                    print(f"Stream Fetch Error: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(streams_result).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
