"""Generate missing WebP variants for images in static/images.

This script is intentionally small and dependency-light for Cloudflare Pages:
install dependencies from requirements.txt, then run `python update_index.py`.
"""

import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).parent
DEFAULT_IMAGES_DIR = BASE_DIR / "static" / "images"
SOURCE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
WEBP_QUALITY = 82


def webp_target_for(image_path):
    return image_path.with_suffix(".webp")


def pillow_is_available():
    return importlib.util.find_spec("PIL") is not None


def convert_to_webp(source_path, target_path):
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(target_path, "WEBP", quality=WEBP_QUALITY, method=6)
    except (OSError, UnidentifiedImageError) as exc:
        return exc
    return None


def generate_webp_images(images_dir=DEFAULT_IMAGES_DIR, strict=True):
    images_dir = Path(images_dir)
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    created = []
    skipped = []
    failed = []

    sources = [
        source_path
        for source_path in sorted(images_dir.iterdir())
        if source_path.is_file() and source_path.suffix.lower() in SOURCE_EXTENSIONS
    ]
    missing_sources = [source_path for source_path in sources if not webp_target_for(source_path).exists()]

    if missing_sources and not pillow_is_available():
        message = "Pillow is required to generate missing WebP variants. Run `python -m pip install -r requirements.txt`."
        if strict:
            raise RuntimeError(message)
        failed.extend((source_path, RuntimeError(message)) for source_path in missing_sources)
        skipped.extend(webp_target_for(source_path) for source_path in sources if webp_target_for(source_path).exists())
        return created, skipped, failed

    for source_path in sources:
        target_path = webp_target_for(source_path)
        if target_path.exists():
            skipped.append(target_path)
            continue

        exc = convert_to_webp(source_path, target_path)
        if exc:
            failed.append((source_path, exc))
            continue
        created.append(target_path)

    return created, skipped, failed


def main():
    created, skipped, failed = generate_webp_images(strict=True)

    for path in created:
        print(f"✅ WebP généré: {path.relative_to(BASE_DIR)}")
    for path in skipped:
        print(f"↪️ WebP déjà présent: {path.relative_to(BASE_DIR)}")
    for source_path, exc in failed:
        print(f"⚠️ Conversion WebP ignorée pour {source_path.relative_to(BASE_DIR)}: {exc}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
