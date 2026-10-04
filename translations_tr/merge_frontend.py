"""Merge Turkish translation fragments into the frontend tr.json locale.

Usage (from repo root):
    python translations_tr/merge_frontend.py            # merge + report
    python translations_tr/merge_frontend.py --list     # list untranslated keys by namespace
    python translations_tr/merge_frontend.py --namespace header   # list untranslated keys in one namespace

Fragment files: translations_tr/frontend/*.json — flat {key: turkish_value}.
Validation per fragment key:
  - key must exist in en.json
  - {{placeholder}} set must be identical to en.json's
  - duplicate key in another fragment -> error
Output: tr.json keeps en.json's key order; untranslated keys keep the English value.
"""

import glob
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EN = REPO / "src/frontend/src/locales/en.json"
TR = REPO / "src/frontend/src/locales/tr.json"
FRAGMENTS_DIR = REPO / "translations_tr/frontend"

PLACEHOLDER_RE = re.compile(r"\{\{\s*[\w.]+\s*\}\}")


def placeholders(value: str) -> list[str]:
    return sorted(m.replace("[{}\s]", "") for m in PLACEHOLDER_RE.findall(value))


def load_fragments() -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in sorted(glob.glob(str(FRAGMENTS_DIR / "*.json"))):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for key, value in data.items():
            if key in merged:
                raise SystemExit(f"ERROR: duplicate key across fragments: {key}")
            merged[key] = value
    return merged


def main() -> None:
    args = sys.argv[1:]
    frags = load_fragments()
    en = json.loads(EN.read_text(encoding="utf-8"))

    if "--list" in args:
        by_ns: dict[str, int] = {}
        for key in en:
            if key not in frags or en[key] == frags.get(key):
                ns = key.split(".")[0]
                by_ns[ns] = by_ns.get(ns, 0) + 1
        for ns, count in sorted(by_ns.items(), key=lambda x: -x[1]):
            print(f"{count:5d}  {ns}")
        return

    if "--namespace" in args:
        ns = args[args.index("--namespace") + 1]
        for key in en:
            if key.split(".")[0] == ns and (key not in frags or en[key] == frags.get(key)):
                print(f"{key} = {en[key]!r}")
        return

    errors = []
    for key, value in frags.items():
        if key not in en:
            errors.append(f"unknown key (not in en.json): {key}")
            continue
        if placeholders(en[key]) != placeholders(value):
            errors.append(
                f"placeholder mismatch: {key}\n  en: {en[key]!r}\n  tr: {value!r}"
            )
        if not isinstance(value, str) or not value.strip():
            errors.append(f"empty/invalid value: {key}")
    if errors:
        print("\n".join(f"  - {e}" for e in errors))
        raise SystemExit(f"VALIDATION FAILED: {len(errors)} error(s)")

    tr = {key: frags.get(key, en_val) for key, en_val in en.items()}

    TR.write_text(
        json.dumps(tr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    translated = sum(1 for k in en if k in frags)
    print(
        f"merged {translated}/{len(en)} keys from "
        f"{len(glob.glob(str(FRAGMENTS_DIR / '*.json')))} fragments"
    )
    print(f"still English-valued: {sum(1 for k in en if k not in frags or tr[k] == en[k])}")


if __name__ == "__main__":
    main()
