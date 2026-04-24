from __future__ import annotations

from collections.abc import Callable

from pickpic.core.scan_control import ScanController


def _hamming_distance(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


def _connected_components(edges: dict[int, set[int]]) -> list[list[int]]:
    groups: list[list[int]] = []
    seen: set[int] = set()

    for start in edges:
        if start in seen:
            continue
        stack = [start]
        group: list[int] = []
        seen.add(start)

        while stack:
            node = stack.pop()
            group.append(node)
            for neighbor in edges[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)

        if len(group) > 1:
            groups.append(sorted(group))

    return groups


def find_hash_groups(
    records: list[dict],
    hash_distance_exact: int = 0,
    hash_distance_similar: int = 10,
    progress_cb: Callable[[int, int, str], None] | None = None,
    controller: ScanController | None = None,
) -> tuple[list[list[int]], list[list[int]]]:
    """
    records: [{id, phash}, ...]
    Returns (exact_groups, similar_groups) — each group is a list of image ids.
    """
    if len(records) < 2:
        return [], []

    by_phash: dict[str, list[int]] = {}
    for row in records:
        by_phash.setdefault(row["phash"], []).append(int(row["id"]))

    exact_groups = [sorted(ids) for ids in by_phash.values() if len(ids) > 1]
    exact_member_ids = {image_id for group in exact_groups for image_id in group}

    remaining = [
        {"id": int(row["id"]), "phash": row["phash"]}
        for row in records
        if int(row["id"]) not in exact_member_ids
    ]
    if len(remaining) < 2:
        if progress_cb:
            progress_cb(1, 1, "Detecting duplicates")
        return exact_groups, []

    edges: dict[int, set[int]] = {row["id"]: set() for row in remaining}
    total_pairs = len(remaining) * (len(remaining) - 1) // 2
    checked_pairs = 0
    last_reported = -1
    if progress_cb:
        progress_cb(0, total_pairs, "Comparing image hashes")
    for i, left in enumerate(remaining):
        if controller:
            controller.checkpoint()
        for right in remaining[i + 1:]:
            if controller:
                controller.checkpoint()
            distance = _hamming_distance(left["phash"], right["phash"])
            if hash_distance_exact < distance <= hash_distance_similar:
                edges[left["id"]].add(right["id"])
                edges[right["id"]].add(left["id"])
            checked_pairs += 1
            if progress_cb and (
                checked_pairs == total_pairs
                or checked_pairs - last_reported >= 1_000
            ):
                last_reported = checked_pairs
                progress_cb(
                    checked_pairs,
                    total_pairs,
                    "Comparing image hashes",
                )

    similar_groups = _connected_components(edges)
    return exact_groups, similar_groups
