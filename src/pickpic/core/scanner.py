from __future__ import annotations

import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pickpic.config import IMAGE_EXTENSIONS, SCAN_CHUNK
from pickpic.core.hasher import compute_hashes
from pickpic.core.blur import compute_blur_score, is_blurry


def _discover_images(
    folders: list[str],
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> list[str]:
    paths = []
    for folder in folders:
        for root, _, files in os.walk(folder):
            for f in files:
                if Path(f).suffix.lower() in IMAGE_EXTENSIONS:
                    p = os.path.join(root, f)
                    paths.append(p)
                    if progress_cb and len(paths) % 50 == 0:
                        progress_cb(0, 0, p)
    return paths


def _process_image(path: str, blur_threshold: float) -> dict | None:
    stat = os.stat(path)
    hashes = compute_hashes(path)
    if hashes is None:
        return None
    score = compute_blur_score(path)
    return {
        "path": path,
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "width": hashes["width"],
        "height": hashes["height"],
        "phash": hashes["phash"],
        "dhash": hashes["dhash"],
        "has_gps": hashes["has_gps"],
        "gps_heading": hashes["gps_heading"],
        "gps_heading_ref": hashes["gps_heading_ref"],
        "is_facing_north": hashes["is_facing_north"],
        "blur_score": score,
        "is_blurry": is_blurry(score, blur_threshold),
    }


def scan_new_only(
    folders: list[str],
    is_cached_fn: Callable[[str, float, int], bool],
    progress_cb: Callable[[int, int, str], None] | None = None,
    workers: int | None = None,
    blur_threshold: float = 100.0,
    min_file_size_bytes: int = 0,
) -> list[dict]:
    """Scan folders, skipping already-cached files."""
    paths = _discover_images(folders, progress_cb)
    to_process = []
    for p in paths:
        try:
            stat = os.stat(p)
            if min_file_size_bytes and stat.st_size < min_file_size_bytes:
                continue
            if not is_cached_fn(p, stat.st_mtime, stat.st_size):
                to_process.append(p)
        except OSError:
            pass

    total_scan = len(paths)
    skipped = total_scan - len(to_process)
    done = skipped
    results = []

    if progress_cb:
        progress_cb(done, total_scan, "")

    if not to_process:
        return results

    workers = workers or min(os.cpu_count() or 4, 8)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_image, p, blur_threshold): p for p in to_process}
        for fut in as_completed(futures):
            p = futures[fut]
            done += 1
            try:
                result = fut.result()
                if result:
                    results.append(result)
            except Exception:
                pass
            if progress_cb:
                progress_cb(done, total_scan, p)

    return results
