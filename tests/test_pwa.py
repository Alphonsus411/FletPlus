import json
from fletplus.web.pwa import generate_service_worker, generate_manifest, register_pwa


class DummyPage:
    def __init__(self):
        self.head = []
        self.scripts = []

    def add_head_html(self, html):
        self.head.append(html)

    def add_script(self, script):
        self.scripts.append(script)


def test_generate_service_worker_and_manifest(tmp_path):
    sw = generate_service_worker(["/", "/main.css"], tmp_path)
    assert sw.exists()
    assert "CACHE_NAME" in sw.read_text()

    icons = [{"src": "icon.png", "sizes": "192x192", "type": "image/png"}]
    manifest = generate_manifest("App", icons, "/", tmp_path)
    data = json.loads(manifest.read_text())
    assert data["name"] == "App"
    assert data["start_url"] == "/"


def test_register_pwa_adds_scripts():
    page = DummyPage()
    register_pwa(page)
    assert any("manifest" in h for h in page.head)
    assert any("serviceWorker" in s for s in page.scripts)
