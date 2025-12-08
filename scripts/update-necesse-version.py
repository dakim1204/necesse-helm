#!/usr/bin/env python3
import re
import sys
from pathlib import Path

import requests
import yaml

DOCKER_NAMESPACE = "brammys"
DOCKER_REPO = "necesse-server"
DOCKER_TAGS_API = f"https://hub.docker.com/v2/repositories/{DOCKER_NAMESPACE}/{DOCKER_REPO}/tags?page_size=100"


def fetch_tags():
    resp = requests.get(DOCKER_TAGS_API, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [r["name"] for r in data.get("results", [])]


def parse_version(tag: str):
    m = re.match(r"^(\d+-\d+-\d+)(?:-(\d+))?$", tag)
    if not m:
        return None

    base = m.group(1)
    build_str = m.group(2)
    major, minor, patch = map(int, base.split("-"))
    build = int(build_str) if build_str is not None else 0
    return (major, minor, patch, build, base, tag)


def select_latest_tag(tags):
    parsed = []
    for t in tags:
        v = parse_version(t)
        if v:
            parsed.append(v)

    if not parsed:
        raise RuntimeError("No parsable Necesse tags found from Docker Hub")

    parsed.sort()
    latest = parsed[-1]
    major, minor, patch, build, base, full_tag = latest
    return base, full_tag


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
    tags = fetch_tags()
    base_version, full_tag = select_latest_tag(tags)

    print(f"Latest Necesse version (base): {base_version}")
    print(f"Latest Docker tag: {full_tag}")

    chart_path = Path("Chart.yaml")
    values_path = Path("values.yaml")

    if not chart_path.exists() or not values_path.exists():
        print("Chart.yaml or values.yaml not found in current directory", file=sys.stderr)
        sys.exit(1)

    # Chart.yaml: appVersion update
    old_app, new_app = update_yaml_file(chart_path, ("appVersion",), base_version)
    print(f"Chart.yaml: appVersion {old_app!r} -> {new_app!r}")

    # values.yaml: image.tag update
    old_tag, new_tag = update_yaml_file(values_path, ("image", "tag"), full_tag)
    print(f"values.yaml: image.tag {old_tag!r} -> {new_tag!r}")

    if old_app == new_app and old_tag == new_tag:
        print("No changes detected.")
    else:
        print("Version files updated.")


if __name__ == "__main__":
    main()

