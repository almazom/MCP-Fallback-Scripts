#!/usr/bin/env python3
"""OCR cache manager for Telegram media assets."""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "telegram_cache" / "media_ocr_cache.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class OCRCache:
    """Small helper around a JSON-based OCR cache."""

    def __init__(self, cache_path: Optional[Path] = None) -> None:
        self.cache_path = cache_path or DEFAULT_CACHE_PATH
        self.data: Dict[str, Dict] = {"version": 1, "entries": {}}
        self.dirty = False
        self._load()

    def _load(self) -> None:
        if self.cache_path.exists():
            try:
                self.data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"⚠️  Failed to read OCR cache ({exc}), starting fresh", file=sys.stderr)
                self.data = {"version": 1, "entries": {}}

    def _key(self, channel: str, message_id: int) -> str:
        return f"{channel}|{message_id}"

    def get_entry(self, channel: str, message_id: int) -> Optional[Dict]:
        return self.data.get("entries", {}).get(self._key(channel, message_id))

    def upsert_entry(self, channel: str, message_id: int, payload: Dict) -> bool:
        entries = self.data.setdefault("entries", {})
        key = self._key(channel, message_id)
        existing = entries.get(key)
        if existing == payload:
            return False
        payload = dict(payload)
        payload["channel"] = channel
        payload["message_id"] = message_id
        entries[key] = payload
        self.dirty = True
        return True

    def save(self) -> None:
        if not self.dirty:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.dirty = False


def find_latest_cache(channel: str) -> Optional[Path]:
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"
    clean_channel = channel.replace('@', '').replace('/', '_')
    matched = sorted(
        cache_dir.glob(f"{clean_channel}_*.json"),
        key=lambda p: p.stat().st_mtime
    )
    return matched[-1] if matched else None


def load_messages(channel: str, filter_type: str) -> List[Dict]:
    cache_file = find_latest_cache(channel)
    if not cache_file:
        raise FileNotFoundError(f"No cache file found for {channel} - run telegram_fetch.py with --fetch-media first")

    data = json.loads(cache_file.read_text(encoding="utf-8"))
    messages = data.get("messages", [])

    from datetime import datetime, timedelta

    def parse(date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    filtered: List[Dict]
    if filter_type == "today":
        target = datetime.now().strftime("%Y-%m-%d")
        filtered = [m for m in messages if m["date_msk"].startswith(target)]
    elif filter_type == "yesterday":
        target = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        filtered = [m for m in messages if m["date_msk"].startswith(target)]
    elif filter_type.startswith("last:"):
        days = int(filter_type.split(":", 1)[1])
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [m for m in messages if parse(m["date_msk"]) >= cutoff]
    elif filter_type == "all":
        filtered = messages
    else:
        filtered = [m for m in messages if m["date_msk"].startswith(filter_type)]

    filtered.sort(key=lambda m: m["date_msk"])
    return filtered


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}


def compute_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_metadata(path: Path) -> Dict:
    try:
        from PIL import Image
    except ImportError:
        return {}

    try:
        with Image.open(path) as img:
            width, height = img.size
            fmt = img.format
        return {"width": width, "height": height, "format": fmt}
    except Exception:
        return {}


def perform_ocr(path: Path, lang: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        from PIL import Image
    except ImportError:
        return None, "Pillow not installed"

    try:
        import pytesseract
    except ImportError:
        return None, "pytesseract not installed"

    langs_to_try = [lang]
    if lang != "eng":
        langs_to_try.append("eng")

    last_error: Optional[str] = None
    for candidate in langs_to_try:
        try:
            with Image.open(path) as img:
                text = pytesseract.image_to_string(img, lang=candidate)
            return text.strip(), None
        except Exception as exc:
            last_error = str(exc)
    return None, last_error or "Unknown OCR error"


def process_media(channel: str, messages: Iterable[Dict], cache: OCRCache, *, refresh: bool, lang: str, limit: Optional[int] = None) -> List[Dict]:
    results: List[Dict] = []
    processed = 0

    for message in messages:
        if limit is not None and processed >= limit:
            break

        media = message.get("media_info") or {}
        file_path = media.get("file_path")
        if not file_path:
            continue

        media_path = Path(file_path)
        if not media_path.exists():
            results.append({
                "message_id": message["id"],
                "status": "missing_file",
                "detail": str(media_path)
            })
            continue

        if not is_image_file(media_path):
            results.append({
                "message_id": message["id"],
                "status": "unsupported",
                "detail": media_path.suffix
            })
            continue

        content_hash = media.get("content_hash") or compute_hash(media_path)
        existing = cache.get_entry(channel, message["id"])
        if existing and existing.get("content_hash") == content_hash and not refresh:
            results.append({
                "message_id": message["id"],
                "status": "cache_hit",
                "ocr_text": existing.get("ocr_text", ""),
                "error": existing.get("error"),
                "file": file_path
            })
            processed += 1
            continue

        text, error = perform_ocr(media_path, lang)
        meta = image_metadata(media_path)
        payload = {
            "content_hash": content_hash,
            "file_name": media_path.name,
            "file_path": str(media_path),
            "image_metadata": meta,
            "ocr_text": text or "",
            "error": error,
            "lang": lang,
            "updated_at": _now_iso()
        }
        changed = cache.upsert_entry(channel, message["id"], payload)
        results.append({
            "message_id": message["id"],
            "status": "updated" if changed else "no_change",
            "ocr_text": text or "",
            "error": error,
            "file": file_path
        })
        processed += 1

    cache.save()
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Cache OCR results for Telegram media")
    parser.add_argument("channel", help="Channel username (with or without @)")
    parser.add_argument("filter", nargs="?", default="today", help="Filter to use when selecting cached messages")
    parser.add_argument("--refresh", action="store_true", help="Re-run OCR even if cache entry exists")
    parser.add_argument("--lang", default="rus+eng", help="Tesseract language codes (default: rus+eng, fallback to eng)")
    parser.add_argument("--limit", type=int, help="Process at most N media messages")
    parser.add_argument("--display", action="store_true", help="Print cached OCR text after processing")
    args = parser.parse_args(argv)

    channel = args.channel if args.channel.startswith('@') else f"@{args.channel}"

    try:
        messages = load_messages(channel, args.filter)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    media_messages = [m for m in messages if m.get("media_info")]
    if not media_messages:
        print("📭 No media messages found for the selected filter")
        return 0

    cache = OCRCache()
    results = process_media(channel, media_messages, cache, refresh=args.refresh, lang=args.lang, limit=args.limit)

    hits = sum(1 for r in results if r["status"] == "cache_hit")
    updated = sum(1 for r in results if r["status"] == "updated")
    unsupported = sum(1 for r in results if r["status"] == "unsupported")
    missing = sum(1 for r in results if r["status"] == "missing_file")
    errors = sum(1 for r in results if r.get("error"))

    print(f"🧾 Media messages processed: {len(results)} (cache hits: {hits}, updated: {updated}, unsupported: {unsupported}, missing files: {missing})")
    if errors:
        print(f"⚠️  {errors} messages have OCR errors (run with --refresh after installing dependencies)")

    if args.display:
        for res in results:
            ocr = (res.get("ocr_text") or "").strip()
            if ocr:
                snippet = ocr if len(ocr) <= 200 else ocr[:197] + "..."
                print(f"\n[id {res['message_id']}] {snippet}")
            elif res.get("error"):
                print(f"\n[id {res['message_id']}] OCR error: {res['error']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
