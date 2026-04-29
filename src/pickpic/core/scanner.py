from __future__ import annotations

import os
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from pickpic.config import IMAGE_EXTENSIONS
from pickpic.core.blur import compute_blur_score, is_blurry
from pickpic.core.hasher import compute_hashes
from pickpic.core.scan_control import ScanController


def _discover_images(
    folders: list[str],
    progress_cb: Callable[[int, int, str], None] | None = None,
    controller: ScanController | None = None,
) -> list[str]:
    paths = []
    for folder in folders:
        for root, _, files in os.walk(folder):
            if controller:
                controller.checkpoint()
            for f in files:
                if controller:
                    controller.checkpoint()
                if Path(f).suffix.lower() in IMAGE_EXTENSIONS:
                    p = os.path.join(root, f)
                    paths.append(p)
                    if progress_cb and len(paths) % 50 == 0:
                        progress_cb(0, 0, p)
    return paths


def _process_image(
    path: str,
    blur_threshold: float,
    feature_blur: bool = True,
    feature_gps: bool = True,
) -> dict | None:
    stat = os.stat(path)
    hashes = compute_hashes(path, extract_gps=feature_gps)
    if hashes is None:
        return None

    if feature_blur:
        score = compute_blur_score(path)
    else:
        score = None

    return {
        "path": path,
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "width": hashes["width"],
        "height": hashes["height"],
        "phash": hashes["phash"],
        "dhash": hashes["dhash"],
        "has_gps": hashes["has_gps"],
        "gps_lat": hashes["gps_lat"],
        "gps_lon": hashes["gps_lon"],
        "gps_heading": hashes["gps_heading"],
        "gps_heading_ref": hashes["gps_heading_ref"],
        "is_facing_north": hashes["is_facing_north"],
        "blur_score": score,
        "is_blurry": is_blurry(score, blur_threshold) if feature_blur else False,
    }


def scan_new_only(
    folders: list[str],
    is_cached_fn: Callable[[str, float, int], bool],
    progress_cb: Callable[[int, int, str], None] | None = None,
    workers: int | None = None,
    blur_threshold: float = 100.0,
    min_file_size_bytes: int = 0,
    controller: ScanController | None = None,
    feature_blur: bool = True,
    feature_gps: bool = True,
) -> list[dict]:
    """Scan folders, skipping already-cached files."""
    paths = _discover_images(folders, progress_cb, controller=controller)
    to_process = []
    for p in paths:
        if controller:
            controller.checkpoint()
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
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        pending_paths = iter(to_process)
        futures: dict = {}

        def submit_more():
            while len(futures) < workers:
                try:
                    path = next(pending_paths)
                except StopIteration:
                    return
                if controller:
                    controller.checkpoint()
                futures[pool.submit(
                    _process_image, path, blur_threshold,
                    feature_blur=feature_blur, feature_gps=feature_gps,
                )] = path

        submit_more()
        try:
            while futures:
                if controller:
                    controller.checkpoint()
                completed, _ = wait(
                    tuple(futures),
                    timeout=0.1,
                    return_when=FIRST_COMPLETED,
                )
                if not completed:
                    continue
                for fut in completed:
                    p = futures.pop(fut)
                    done += 1
                    try:
                        result = fut.result()
                        if result:
                            results.append(result)
                    except Exception:
                        pass
                    if progress_cb:
                        progress_cb(done, total_scan, p)
                submit_more()
        finally:
            for fut in futures:
                fut.cancel()
    except Exception:
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        pool.shutdown(wait=True)

    return results
