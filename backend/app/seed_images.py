"""Upload deterministic placeholder images used by the MVP seed dataset."""

from __future__ import annotations

import argparse
from html import escape

from app.core.config import get_settings
from app.integrations.image_storage import FilebaseImageStorage

IMAGE_NUMBERS = range(3, 121, 3)
CATEGORIES = ["ROAD_DAMAGE", "WASTE", "WATER_SUPPLY", "STREETLIGHT", "DRAINAGE"]
COLORS = {
    "ROAD_DAMAGE": ("#5B4636", "#E8C39E"),
    "WASTE": ("#2F6B3C", "#B8E0C2"),
    "WATER_SUPPLY": ("#2166A5", "#B9DDF5"),
    "STREETLIGHT": ("#5A4A8A", "#DDD2FF"),
    "DRAINAGE": ("#34545C", "#B9D8D6"),
}


def image_key(number: int) -> str:
    return f"seed-images/complaint-{number:03d}.svg"


def legacy_image_key(number: int) -> str:
    return f"seed-images/complaint-{number:03d}.jpg"


def image_category(number: int) -> str:
    return CATEGORIES[((number // 3) - 1) % len(CATEGORIES)]


def svg_image(category: str, number: int) -> bytes:
    foreground, background = COLORS[category]
    label = escape(category.replace("_", " "))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
<rect width="1200" height="800" fill="{background}"/>
<rect x="48" y="48" width="1104" height="704" rx="32" fill="{foreground}" opacity="0.94"/>
<circle cx="600" cy="330" r="150" fill="{background}" opacity="0.9"/>
<path d="M470 470 Q600 380 730 470" fill="none" stroke="{foreground}" stroke-width="28" stroke-linecap="round"/>
<text x="600" y="620" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" font-weight="700" fill="white">{label}</text>
<text x="600" y="685" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" fill="white">Civic SahAI MVP image {number:03d}</text>
</svg>"""
    return svg.encode("utf-8")


def upload_seed_images() -> int:
    settings = get_settings()
    if settings.image_storage_provider.lower() != "filebase":
        raise RuntimeError("IMAGE_STORAGE_PROVIDER must be filebase to upload seed images")
    if not settings.filebase_access_key_id or not settings.filebase_secret_access_key:
        raise RuntimeError("FILEBASE_ACCESS_KEY_ID and FILEBASE_SECRET_ACCESS_KEY are required")

    storage = FilebaseImageStorage(
        endpoint_url=settings.filebase_endpoint_url,
        access_key_id=settings.filebase_access_key_id,
        secret_access_key=settings.filebase_secret_access_key,
        region=settings.filebase_region,
        signature_version=settings.filebase_signature_version,
        bucket=settings.filebase_bucket,
    )
    count = 0
    for number in IMAGE_NUMBERS:
        image = svg_image(image_category(number), number)
        storage.upload(image_key(number), image, "image/svg+xml")
        # Earlier MVP seed rows used .jpg keys; retain aliases for those rows.
        storage.upload(legacy_image_key(number), image, "image/svg+xml")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload MVP complaint images to Filebase")
    parser.parse_args()
    print(f"Uploaded {upload_seed_images()} MVP complaint images to Filebase")


if __name__ == "__main__":
    main()
