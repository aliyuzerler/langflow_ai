"""Build the 'Sosyal Medya Pazarlama Agentı' flow from the Twitter Thread
Generator starter and POST it to the running Langflow instance.

Usage: python -m uv run python translations_tr/make_marketing_flow.py
"""

import json
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:7860"
SRC = Path(__file__).parent.parent / "src/backend/base/langflow/initial_setup/starter_projects/Twitter Thread Generator.json"

SYSTEM_PROMPT = """Sen uzman bir sosyal medya pazarlama danışmanısın. Kullanıcının verdiği brief'e göre X (Twitter), Instagram, Facebook ve LinkedIn platformları için pazarlama içerikleri üret.

## Çalışma kuralları
1. Brief'ten hedef kitleyi, tonu ve öne çıkan faydayı çıkar; eksik bilgi varsa makul varsayımlar yap ve çıktının başında kısaca belirt.
2. Her platform için o platforma özgü format ve en iyi uygulamaları izle.
3. Her platform için 2 varyant üret: A) doğrudan/satış odaklı, B) hikâye/eğlence odaklı.
4. Emoji ve hashtag kullanımında platform normuna uy; spam yapma.
5. Çıktının sonuna "📌 Yayın Önerileri" bölümü ekle: önerilen paylaşım gün/saatleri ve platformlar arası içerik uyarlaması notları.

## Platform formatları
### X (Twitter)
- Gönderi başına en fazla 280 karakter (karakter sayısını belirt)
- Kanca ilk cümlede, tek ve güçlü bir CTA
- A varyantı: tek gönderi + 3-5 hashtag; B varyantı: 5-7 tweet'lik thread taslağı

### Instagram
- Caption: kanca + kısa paragraflar + satır araları
- 10-15 hashtag (geniş erişimli + niş karışımı)
- Görsel/carousel önerisi (format, kompozisyon, metin katmanı)

### Facebook
- Daha uzun, hikâye anlatan metin (80-150 kelime)
- CTA buton önerisi ("Şimdi Keşfet", "Mesaj Gönder" vb.)
- 2-4 hashtag

### LinkedIn
- Profesyonel ton; sorun → çözüm → sonuç yapısı
- Sektörel çerçeve; veri gerekiyorsa [VERİ] yer tutucusu kullan, asla uydurma
- Kişisel marka ve şirket sayfası için ayrı uyarlama notu

## Çıktı formatı
Platform başlıkları: "## 🐦 X", "## 📸 Instagram", "## 📘 Facebook", "## 💼 LinkedIn".
Varyantları "A)" ve "B)" olarak etiketle."""

CHAT_DEFAULT = """**Görev:** Yeni bir ürünü/kampanyayı duyur

**Ürün / Kampanya:** [ürünü kısaca tanıt]
**Hedef kitle:** [kimlere ulaşmak istiyorsun]
**Ton:** [örn. samimi, profesyonel, eğlenceli]
**Öne çıkan fayda:** [neden bu ürün?]"""

NOTE_TEXT = """# 📣 Sosyal Medya Pazarlama Agent'ı

X, Instagram, Facebook ve LinkedIn için pazarlama içerikleri üretir.

## Kurulum
1. **Agent** düğümünde **Model** seç ve API anahtarını gir (Sağlayıcıyı Kur).
2. **Chat Input**'a ürün/kampanya brief'ini yaz.
3. **Playground**'u aç ve çalıştır.

Prompt düğümündeki sistem talimatlarından platform kurallarını özelleştirebilirsin."""


def main() -> None:
    flow = json.loads(SRC.read_text(encoding="utf-8"))

    flow["name"] = "Sosyal Medya Pazarlama Agent'ı"
    flow["description"] = (
        "X (Twitter), Instagram, Facebook ve LinkedIn için platforma özgü pazarlama "
        "içerikleri üreten Agent. Brief'ten hedef kitle ve tona uygun 2 varyant + "
        "yayın önerileri döndürür."
    )
    flow["endpoint_name"] = "sosyal-medya-pazarlama-agenti"
    flow["tags"] = ["chatbots", "content-generation", "marketing"]

    for node in flow["data"]["nodes"]:
        nid = node["id"]
        nd = node["data"]["node"]
        if nid.startswith("Prompt-"):
            nd["template"]["template"]["value"] = SYSTEM_PROMPT
            nd["description"] = "Sosyal medya pazarlama sistem talimatları (Türkçe)"
        elif nid.startswith("ChatInput-"):
            nd["template"]["input_value"]["value"] = CHAT_DEFAULT
        elif nid.startswith("Agent-"):
            nd["template"]["system_prompt"]["value"] = ""
        elif nid.startswith("note-"):
            nd["description"] = NOTE_TEXT

    # auth token
    token = json.loads(
        urllib.request.urlopen(f"{BASE}/api/v1/auto_login").read()
    )["access_token"]

    payload = {
        "name": flow["name"],
        "description": flow["description"],
        "endpoint_name": flow["endpoint_name"],
        "is_component": False,
        "tags": flow["tags"],
        "data": flow["data"],
    }
    req = urllib.request.Request(
        f"{BASE}/api/v1/flows/",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    print("CREATED:", resp.get("name"), "| id:", resp.get("id"))


if __name__ == "__main__":
    main()
