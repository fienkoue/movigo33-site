import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STATIC_IMAGES_DIR = BASE_DIR / "static" / "images"
DIST_DIR = BASE_DIR / "dist"
DIST_IMAGES_DIR = DIST_DIR / "static" / "images"


def load_json(name):
    with (DATA_DIR / name).open("r", encoding="utf-8") as file:
        return json.load(file)


def iter_image_references(data, source, path=""):
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if key in {"image", "image_file"} and isinstance(value, str) and value:
                yield source, current_path, value
            else:
                yield from iter_image_references(value, source, current_path)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            current_path = f"{path}[{index}]" if path else f"[{index}]"
            yield from iter_image_references(item, source, current_path)


def dist_html_files():
    if not DIST_DIR.exists():
        return []
    return sorted(DIST_DIR.rglob("*.html"))


def filename_is_referenced_in_dist(filename, html_files):
    pattern = re.compile(rf"/static/images/{re.escape(filename)}(?:[\"'?#<\s]|$)")
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        if pattern.search(content):
            return True
    return False


def main():
    references = [
        *iter_image_references(load_json("produits.json"), "data/produits.json"),
        *iter_image_references(load_json("posts.json"), "data/posts.json"),
    ]
    html_files = dist_html_files()
    errors = []

    for source, path, filename in references:
        if not (STATIC_IMAGES_DIR / filename).is_file():
            errors.append(f"{source}:{path} references missing static image: {filename}")
        if not (DIST_IMAGES_DIR / filename).is_file():
            errors.append(f"{source}:{path} is not copied to dist/static/images: {filename}")
        if html_files and not filename_is_referenced_in_dist(filename, html_files):
            errors.append(f"{source}:{path} is not referenced in any dist HTML file: {filename}")

    if errors:
        print("❌ Image reference validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"✅ {len(references)} image references exist in static/images, dist/static/images, and dist HTML.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
