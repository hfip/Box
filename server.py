import os
from http.server import HTTPServer
from api.index import handler

def run():
    # Render يمرر المنفذ تلقائياً عبر متغيرات البيئة PORT
    port = int(os.environ.get("PORT", 7860))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, handler)
    print(f"MovieBox Cloud Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
