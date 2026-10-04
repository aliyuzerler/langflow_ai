"""Extract key->English map for backend component translations (core + bundles).

Mirrors scripts/gp/extract_backend_strings.py but:
  - also walks installed lfx-* bundle component packages
  - writes to translations_tr/backend_en.json (never touches locales/en.json)

Run from repo root: python -m uv run python translations_tr/extract_backend_en.py
"""

from __future__ import annotations

import importlib
import json
from importlib.metadata import distributions
from pathlib import Path

OUT = Path(__file__).parent / "backend_en.json"


def collect_from_package(components_pkg) -> dict[str, str]:
    import pkgutil

    from langflow.utils.i18n_keys import component_field_key, normalize_component_key

    flat: dict[str, str] = {}
    for _finder, modname, _ispkg in pkgutil.walk_packages(
        components_pkg.__path__, components_pkg.__name__ + "."
    ):
        if "deactivated" in modname:
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as e:  # noqa: BLE001
            print(f"  SKIP {modname}: {e}")
            continue

        for cls in vars(module).values():
            if not isinstance(cls, type):
                continue
            if getattr(cls, "__module__", None) != modname:
                continue
            if not getattr(cls, "code_class_base_inheritance", None):
                continue
            display_name = getattr(cls, "display_name", None)
            if not isinstance(display_name, str) or not display_name:
                continue
            component_key = getattr(cls, "name", None) or cls.__name__
            if not isinstance(component_key, str):
                component_key = cls.__name__
            norm_key = normalize_component_key(component_key)

            flat[component_field_key(norm_key, "display_name", display_name)] = display_name
            raw_desc = cls.__dict__.get("description")
            if isinstance(raw_desc, property):
                description = getattr(cls, "_base_description", "") or ""
            else:
                description = getattr(cls, "description", "") or ""
            if isinstance(description, str) and description:
                flat[component_field_key(norm_key, "description", description)] = description

            for inp in getattr(cls, "inputs", []) or []:
                field_name = getattr(inp, "name", None)
                if not (isinstance(field_name, str) and field_name):
                    continue
                for sub in ("display_name", "info", "placeholder"):
                    val = getattr(inp, sub, None)
                    if isinstance(val, str) and val:
                        flat[component_field_key(norm_key, f"inputs.{field_name}.{sub}", val)] = val

            for out in getattr(cls, "outputs", []) or []:
                out_name = getattr(out, "name", None)
                if not (isinstance(out_name, str) and out_name):
                    continue
                for sub in ("display_name", "info"):
                    val = getattr(out, sub, None)
                    if isinstance(val, str) and val:
                        flat[component_field_key(norm_key, f"outputs.{out_name}.{sub}", val)] = val
    return flat


def main() -> None:
    from langflow.utils.i18n_keys import component_field_key, safe_flow_key

    flat: dict[str, str] = {}

    import lfx.components as core_pkg

    core = collect_from_package(core_pkg)
    print(f"core lfx.components: {len(core)} keys")
    flat.update(core)

    bundle_total = 0
    for dist in distributions():
        name = dist.metadata["Name"] or ""
        if not name.startswith("lfx-"):
            continue
        modname = name.replace("-", "_")
        try:
            pkg = importlib.import_module(f"{modname}.components")
        except ImportError:
            continue
        keys = collect_from_package(pkg)
        new = {k: v for k, v in keys.items() if k not in flat}
        print(f"bundle {name}: {len(keys)} keys ({len(new)} new)")
        flat.update(new)
        bundle_total += len(new)
    print(f"bundles total new: {bundle_total}")

    # starter flows + template notes (same tiers as the GP extractor)
    starter_dir = (
        Path(__file__).resolve().parents[1]
        / "src/backend/base/langflow/initial_setup/starter_projects"
    )
    starter = 0
    for project_file in sorted(starter_dir.glob("*.json")):
        project = json.loads(project_file.read_text(encoding="utf-8"))
        pname = project.get("name")
        pdesc = project.get("description", "")
        if pname and isinstance(pname, str):
            key = safe_flow_key(pname)
            flat[f"starter_flows.{key}.name"] = pname
            starter += 1
            if pdesc and isinstance(pdesc, str):
                flat[f"starter_flows.{key}.description"] = pdesc
    notes = 0
    for project_file in sorted(starter_dir.glob("*.json")):
        project = json.loads(project_file.read_text(encoding="utf-8"))
        for node in project.get("data", {}).get("nodes", []):
            if node.get("type") != "noteNode":
                continue
            node_data = node.get("data", {}).get("node", {})
            i18n_key = node_data.get("i18n_key")
            desc = node_data.get("description", "")
            if i18n_key and desc:
                flat[i18n_key] = desc
                notes += 1
    print(f"starter flows: {starter}, template notes: {notes}")

    flat[component_field_key("_toolmode", "outputs.component_as_tool.display_name", "Toolset")] = "Toolset"

    unique_values = len(set(flat.values()))
    print(f"TOTAL: {len(flat)} keys, {unique_values} unique English values")
    OUT.write_text(json.dumps(dict(sorted(flat.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"written {OUT}")


if __name__ == "__main__":
    main()
