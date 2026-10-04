"""Merge backend Turkish translations into src/backend/base/langflow/locales/tr.json.

Inputs:
  translations_tr/backend_en.json      — key -> English (from extract_backend_en.py)
  translations_tr/backend_values/*.json — English -> Turkish value tables (fragments)

Output: backend tr.json — for every key whose English value has a Turkish
translation in the value tables, write key->Turkish. Keys without a translation
are omitted (runtime falls back to en.json / raw English default).

Usage:
    python translations_tr/merge_backend.py            # merge + report
    python translations_tr/merge_backend.py --missing  # dump untranslated values by frequency
"""

import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EN = REPO / "translations_tr/backend_en.json"
TR = REPO / "src/backend/base/langflow/locales/tr.json"
VALUES_DIR = REPO / "translations_tr/backend_values"


def main() -> None:
    en = json.loads(EN.read_text(encoding="utf-8"))

    tables: dict[str, str] = {}
    for path in sorted(glob.glob(str(VALUES_DIR / "*.json"))):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for k, v in data.items():
            if k in tables and tables[k] != v:
                raise SystemExit(f"CONFLICT for {k!r}")
            tables[k] = v

    # a "translation" equal to its source is a deliberate keep-English decision
    out: dict[str, str] = {}
    translated_keys = 0
    for key, english in en.items():
        tr = tables.get(english)
        if tr is not None:
            out[key] = tr
            translated_keys += 1

    TR.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    kept_en = sum(1 for k, v in out.items() if v == en[k])
    print(
        f"backend tr.json: {translated_keys}/{len(en)} keys translated "
        f"({kept_en} intentionally English); {len(en) - translated_keys} fall back to English"
    )

    if "--missing" in sys.argv:
        freq: dict[str, int] = {}
        for english in en.values():
            freq[english] = freq.get(english, 0) + 1
        missing = [(v, c) for v, c in freq.items() if v not in tables]
        missing.sort(key=lambda x: -x[1])
        print(f"{len(missing)} untranslated unique values; top 400 by frequency:")
        for v, c in missing[:400]:
            print(f"{c:3d}x {v[:150]!r}")


if __name__ == "__main__":
    main()
