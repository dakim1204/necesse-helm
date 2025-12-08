#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

import requests
import yaml

DOCKER_NAMESPACE = "brammys"
DOCKER_REPO = "necesse-server"
DOCKER_TAGS_API = f"https://hub.docker.com/v2/repositories/{DOCKER_NAMESPACE}/{DOCKER_REPO}/tags?page_size=100"


def fetch_tags():
    resp = requests.get(DOCKER_TAGS_API, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    tags = []
    for r in results:
        name = r.get("name")
        last_updated_str = r.get("last_updated") or r.get("tag_last_pushed")
        try:
            last_updated = datetime.fromisoformat(
                last_updated_str.replace("Z", "+00:00")
            )
        except Exception:
            last_updated = datetime(1970, 1, 1, tzinfo=timezone.utc)

        tags.append(
            {
                "name": name,
                "last_updated": last_updated,
            }
        )
    return tags


def parse_version(tag: str):
    m = re.match(r"^(\d+-\d+-\d+)(?:-(\d+))?$", tag)
    if not m:
        return None

    base = m.group(1)
    build_str = m.group(2)
    major, minor, patch = map(int, base.split("-"))
    build = int(build_str) if build_str is not None else 0
    # (major, minor, patch, build, base, full_tag)
    return major, minor, patch, build, base, tag


def select_latest_tag(tag_records):
    parsed = []
    for rec in tag_records:
        name = rec["name"]
        last_updated = rec["last_updated"]
        v = parse_version(name)
        if not v:
            continue
        major, minor, patch, build, base, full_tag = v
        parsed.append(
            {
                "name": full_tag,
                "base": base,
                "major": major,
                "minor": minor,
                "patch": patch,
                "build": build,
                "last_updated": last_updated,
            }
        )

    if not parsed:
        raise RuntimeError("No parsable Necesse tags found from Docker Hub")

    parsed.sort(key=lambda x: x["last_updated"])
    latest_time = parsed[-1]["last_updated"]

    latest_candidates = [
        p for p in parsed if p["last_updated"] == latest_time
    ]

    latest_candidates.sort(
        key=lambda x: (x["major"], x["minor"], x["patch"], x["build"])
    )
    chosen = latest_candidates[-1]

    base_version = chosen["base"]
    full_tag = chosen["name"]
    return base_version, full_tag


def update_yaml_file(path: Path, field_path, new_value):
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    node = content
    for key in field_path[:-1]:
        if key not in node:
            node[key] = {}
        node = node[key]
    last = field_path[-1]
    old_value = node.get(last)
    node[last] = new_value
    path.write_text(
        yaml.safe_dump(content, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return old_value, new_value


def main():
    print("Fetching tags from Docker Hub...")
    tag_records = fetch_tags()
    base_version, full_tag = select_latest_tag(tag_records)

    print(f"Latest Necesse base version (by date): {base_version}")
    print(f"Latest Docker tag (by date + version): {full_tag}")

    chart_path = Path("Chart.yaml")
    values_path = Path("values.yaml")

    if not chart_path.exists() or not values_path.exists():
        print("Chart.yaml or values.yaml not found in current directory", file=sys.stderr)
        sys.exit(1)

    old_app, new_app = update_yaml_file(chart_path, ("appVersion",), base_version)
    print(f"Chart.yaml: appVersion {old_app!r} -> {new_app!r}")

    old_tag, new_tag = update_yaml_file(values_path, ("image", "tag"), full_tag)
    print(f"values.yaml: image.tag {old_tag!r} -> {new_tag!r}")

    if old_app == new_app and old_tag == new_tag:
        print("No changes detected.")
    else:
        print("Version files updated.")


if __name__ == "__main__":
    main()
