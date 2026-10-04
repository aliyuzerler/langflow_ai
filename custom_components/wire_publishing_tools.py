"""Sosyal Medya Pazarlama Agent'ı akışına paylaşım tool'larını bağlar.

custom_components/ altındaki 4 bileşeni (Facebook/Instagram/LinkedIn/X)
akışa düğüm olarak ekler, Agent'ın tools girişine bağlar ve sistem
prompt'una yayın kurallarını işler. Tekrar çalıştırılabilir (idempotent):
önceden eklenmiş düğümleri yeniden eklemez, prompt'u güncel tutar.
"""

import json
import random
import string
import urllib.request

BASE = "http://127.0.0.1:7860"
FLOW_ID = "f08e1b34-05db-4f2e-ab87-f5747145ae7c"
COMPONENTS = ["FacebookPost", "InstagramPost", "LinkedInPost", "XPost"]
POSITIONS = {
    "FacebookPost": (660, 1450),
    "InstagramPost": (660, 1720),
    "LinkedInPost": (660, 1990),
    "XPost": (660, 2260),
}

PUBLISH_RULES = """

## Yayınlama Araçları
Sana bağlı sosyal medya paylaşım tool'ları var: facebook_post, instagram_post, linkedin_post, x_post.

Kurallar:
1. İçeriği üret ve kullanıcıya göster. Aracı (tool) SADECE kullanıcı açıkça "yayınla / paylaş / onayla" derse çağır; kendiliğinden paylaşma.
2. Tool'lar varsayılan olarak dry_run (deneme) modundadır: yalnızca paylaşılacak içeriğin önizlemesini dönerler. Gerçek paylaşım için ilgili bileşen düğümündeki "Deneme Modu (dry_run)" kapatılmalıdır.
3. Instagram gönderisi görsel gerektirir: geçerli bir görsel URL'si yoksa paylaşma, kullanıcıdan iste.
4. X (Twitter) için 280 karakter sınırını aşan metni kısalt ve kullanıcıya haber ver.
5. Paylaşım sonrası dönen bağlantıyı (permalink) mutlaka kullanıcıya ilet."""


def req_json(url, token, method="GET", payload=None):
    import gzip

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = urllib.request.Request(
        url, data=json.dumps(payload).encode() if payload else None, headers=headers, method=method
    )
    body = urllib.request.urlopen(r).read()
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    return json.loads(body)


def rid():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


def main() -> None:
    token = json.loads(urllib.request.urlopen(f"{BASE}/api/v1/auto_login").read())["access_token"]
    catalog = req_json(f"{BASE}/api/v1/all", token)
    templates = {}
    for comps in catalog.values():
        for name, nd in comps.items():
            if name in COMPONENTS:
                templates[name] = nd

    missing = [c for c in COMPONENTS if c not in templates]
    if missing:
        raise SystemExit(f"Katalogda bulunamadı: {missing}")

    flow = req_json(f"{BASE}/api/v1/flows/{FLOW_ID}", token)
    data = flow["data"]
    agent_id = next(n["id"] for n in data["nodes"] if n["id"].startswith("Agent-"))

    existing = {n["data"]["node"].get("key") or n["data"]["node"].get("type") for n in data["nodes"]}
    envelope_ref = next(n for n in data["nodes"] if n["id"].startswith("Prompt-"))

    for name in COMPONENTS:
        if name in existing:
            print(f"zaten ekli: {name}")
            continue
        node_id = f"{name}-{rid()}"
        nd = json.loads(json.dumps(templates[name]))
        node = {
            "id": node_id,
            "type": "genericNode",
            "position": {"x": POSITIONS[name][0], "y": POSITIONS[name][1]},
            "positionAbsolute": {"x": POSITIONS[name][0], "y": POSITIONS[name][1]},
            "selected": False,
            "dragging": False,
            "data": {"id": node_id, "node": nd},
        }
        data["nodes"].append(node)
        src_handle = "{œdataTypeœ: œ%sœ, œidœ: œ%sœ, œnameœ: œtoolsœ, œoutput_typesœ: [œToolœ]}" % (name, node_id)
        tgt_handle = "{œfieldNameœ: œtoolsœ, œidœ: œ%sœ, œinputTypesœ: [œToolœ], œtypeœ: œotherœ}" % agent_id
        data["edges"].append({
            "animated": False,
            "className": "",
            "data": {
                "sourceHandle": {"dataType": name, "id": node_id, "name": "tools", "output_types": ["Tool"]},
                "targetHandle": {"fieldName": "tools", "id": agent_id, "inputTypes": ["Tool"], "type": "other"},
            },
            "id": f"reactflow__edge-{node_id}{{œdataTypeœ:œ{name}œ,œidœ:œ{node_id}œ,œnameœ:œtoolsœ,œoutput_typesœ:[œToolœ]}}-{agent_id}{{œfieldNameœ:œtoolsœ,œidœ:œ{agent_id}œ,œinputTypesœ:[œToolœ],œtypeœ:œotherœ}}",
            "selected": False,
            "source": node_id,
            "sourceHandle": src_handle,
            "target": agent_id,
            "targetHandle": tgt_handle,
        })
        print(f"eklendi: {node_id}")

    # sistem prompt'una yayın kuralları ekle (idempotent)
    for n in data["nodes"]:
        if n["id"].startswith("Prompt-"):
            val = n["data"]["node"]["template"]["template"]["value"]
            if "Yayınlama Araçları" not in val:
                n["data"]["node"]["template"]["template"]["value"] = val + PUBLISH_RULES
                print("sistem prompt'u güncellendi")

    resp = req_json(f"{BASE}/api/v1/flows/{FLOW_ID}", token, "PATCH", {"data": data})
    print("PATCHED:", resp.get("name"))


if __name__ == "__main__":
    main()
