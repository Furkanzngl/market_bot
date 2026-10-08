"""Image delivery layer for the mobile API.

Original posters remain the source of truth.  This module creates an on-disk,
content-addressed WebP derivative only when a phone asks for it.  The same
poster is therefore downloaded from the upstream CDN once per API server,
rather than once per device.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageOps
from curl_cffi import requests


CACHE_DIR = Path("media_cache")
ALLOWED_HOSTS = ("a101.com.tr", "bim.com.tr", "migros.com.tr")


def image_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


def is_allowed_source(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host and any(host == domain or host.endswith(f".{domain}") for domain in ALLOWED_HOSTS)


def cached_webp(url: str, width: int) -> Path:
    """Return a quality-preserving, bounded-size WebP derivative."""
    if not is_allowed_source(url):
        raise ValueError("Görsel kaynağı izinli bir market CDN'i değil.")
    width = max(160, min(int(width), 1440))
    destination = CACHE_DIR / f"{image_key(url)}-{width}.webp"
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"},
        timeout=30,
        impersonate="chrome120",
    )
    if response.status_code != 200:
        raise RuntimeError(f"Kaynak görsel HTTP {response.status_code} döndürdü.")

    with Image.open(BytesIO(response.content)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        if image.width > width:
            height = round(image.height * width / image.width)
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix="poster-", suffix=".tmp", dir=destination.parent)
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            image.save(temporary, "WEBP", quality=82, method=6)
            # replace is atomic; concurrent requests can safely race to build.
            temporary.replace(destination)
        finally:
            if temporary.exists():
                temporary.unlink()
    return destination
