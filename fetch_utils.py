"""Small reliability helpers shared by the collectors."""
from __future__ import annotations

import json
import os
import random
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CollectorError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_with_retries(session, url: str, *, headers: dict[str, str], attempts: int = 3):
    """Retry temporary failures, but fail fast on source access decisions."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response
            if response.status_code in {401, 403, 404}:
                raise CollectorError(f"HTTP {response.status_code}: {url}")
            last_error = CollectorError(f"HTTP {response.status_code}: {url}")
        except CollectorError:
            raise
        except Exception as exc:
            last_error = exc
        if attempt < attempts - 1:
            time.sleep((2 ** attempt) + random.uniform(0, 0.4))
    raise CollectorError(f"{url} okunamadı: {last_error}")


def atomic_write_json(path: str | Path, data: Any) -> None:
    """Avoid publishing a partly-written JSON file if the job is interrupted."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, separators=(",", ":"))
            file.write("\n")
        os.replace(temporary, target)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def has_usable_payload(data: Any) -> bool:
    return isinstance(data, dict) and any(
        isinstance(data.get(key), list) and data[key]
        for key in ("kampanyalar", "afisler", "kategoriler")
    )
