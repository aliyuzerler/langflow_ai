"""Kırık tool düğümlerini tam starter zarfıyla yeniden kurar."""

import copy
import gzip
import json
import random
import string
import urllib.request

BASE = "http://127.0.0.1:7860"
FLOW_ID = "f08e1b34-05db-4f2e-ab87-f5747145ae7c"
PREFIXES = ("FacebookPost-", "InstagramPost-", "LinkedInPost-", "XPost-")
COMPONENTS = ["FacebookPost", "InstagramPost", "LinkedInPost", "XPost"]
POSITIONS = {
    "FacebookPost": (660, 1450),
    "InstagramPost": (660, 1720),
    "LinkedInPost": (660, 1990),
    "XPost": (660, 2260),
}


def get_json(url, token):
    r = urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}))
    b = r.read()
    if b[:2] == b"\x1f\x8b":
        b = gzip.decompress(b)
    return json.loads(b)


def main() -> None:
    token = json.loads(urllib.request.urlopen(f"{BASE}/api/v1/auto_login").read())["access_token"]
    catalog = get_json(f"{BASE}/api/v1/all", token)
    templates = {}
    for comps in catalog.values():
        for name, nd in comps.items():
            if name in COMPONENTS:
                templates[name] = nd

    flow = get_json(f"{BASE}/api/v1/flows/{FLOW_ID}", token)
    data = flow["data"]

    # 1) kırık düğümleri ve kenarlarını temizle
    bad_ids = {n["id"] for n in data["nodes"] if n["id"].startswith(PREFIXES)}
    data["nodes"] = [n for n in data["nodes"] if n["id"] not in bad_ids]
    data["edges"] = [e for e in data["edges"] if e["source"] not in bad_ids]
    print("temizlendi:", len(bad_ids), "düğüm")

    # 2) sağlam bir düğümü zarf şablonu olarak kullan (Prompt)
    skeleton = next(n for n in data["nodes"] if n["id"].startswith("Prompt-"))
    agent_id = next(n["id"] for n in data["nodes"] if n["id"].startswith("Agent-"))

    for name in COMPONENTS:
        nid = f"{name}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
        pos = {"x": POSITIONS[name][0], "y": POSITIONS[name][1]}
        node = {
            "id": nid,
            "type": "genericNode",
            "position": pos,
            "positionAbsolute": pos,
            "selected": False,
            "dragging": False,
            "measured": {"height": 211, "width": 320},
            "data": {"id": nid, "type": name, "node": copy.deepcopy(templates[name])},
        }
        data["nodes"].append(node)

        src = "{œdataTypeœ: œ%sœ, œidœ: œ%sœ, œnameœ: œtoolsœ, œoutput_typesœ: [œToolœ]}" % (name, nid)
        tgt = "{œfieldNameœ: œtoolsœ, œidœ: œ%sœ, œinputTypesœ: [œToolœ], œtypeœ: œotherœ}" % agent_id
        edge_id = (
            "reactflow__edge-%s{{œdataTypeœ:œ%sœ,œidœ:œ%sœ,œnameœ:œtoolsœ,œoutput_typesœ:[œToolœ]}}-%s"
            "{{œfieldNameœ:œtoolsœ,œidœ:œ%sœ,œinputTypesœ:[œToolœ],œtypeœ:œotherœ}}"
        ) % (nid, name, nid, agent_id, agent_id)
        data["edges"].append({
            "animated": False,
            "className": "",
            "data": {
                "sourceHandle": {"dataType": name, "id": nid, "name": "tools", "output_types": ["Tool"]},
                "targetHandle": {"fieldName": "tools", "id": agent_id, "inputTypes": ["Tool"], "type": "other"},
            },
            "id": edge_id.replace("{{", "{").replace("}}", "}"),
            "selected": False,
            "source": nid,
            "sourceHandle": src,
            "target": agent_id,
            "targetHandle": tgt,
        })
        print("yeniden kuruldu:", nid)

    payload = json.dumps({"data": data}).encode()
    r = urllib.request.Request(
        f"{BASE}/api/v1/flows/{FLOW_ID}", data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="PATCH",
    )
    resp = json.loads(urllib.request.urlopen(r).read())
    print("PATCHED:", resp.get("name"))


if __name__ == "__main__":
    main()
