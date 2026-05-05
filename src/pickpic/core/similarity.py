from __future__ import annotations

from collections.abc import Callable

import hnswlib
import numpy as np

from pickpic.core.scan_control import ScanController

# Threshold below which brute-force is used (HNSW overhead not worthwhile).
_HNSW_MIN_SIZE = 100


def _phash_to_bits(hex_hash: str) -> np.ndarray:
    """Convert a hex pHash string to a 64-dimensional float32 binary vector."""
    val = int(hex_hash, 16)
    return np.array([(val >> i) & 1 for i in range(64)], dtype=np.float32)


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


def _find_similar_bruteforce(
    remaining: list[dict],
    hash_distance_exact: int,
    hash_distance_similar: int,
    progress_cb: Callable[[int, int, str], None] | None,
    controller: ScanController | None,
) -> list[list[int]]:
    """O(n^2) brute-force fallback for small sets."""
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
                progress_cb(checked_pairs, total_pairs, "Comparing image hashes")

    return _connected_components(edges)


def _find_similar_hnsw(
    remaining: list[dict],
    hash_distance_exact: int,
    hash_distance_similar: int,
    progress_cb: Callable[[int, int, str], None] | None,
    controller: ScanController | None,
) -> list[list[int]]:
    """Use HNSW approximate nearest neighbor for fast similarity search."""
    n = len(remaining)
    dim = 64  # pHash is 64 bits

    if progress_cb:
        progress_cb(0, 3, "Building similarity index")

    # Step 1: Build vectors
    vectors = np.empty((n, dim), dtype=np.float32)
    id_list = []
    for idx, row in enumerate(remaining):
        vectors[idx] = _phash_to_bits(row["phash"])
        id_list.append(row["id"])

    if controller:
        controller.checkpoint()

    # Step 2: Build HNSW index
    # L2 distance on binary vectors: ||a - b||^2 = hamming_distance(a, b)
    # So threshold in L2 squared space = hash_distance_similar
    index = hnswlib.Index(space="l2", dim=dim)
    # ef_construction and M tuned for recall vs speed tradeoff
    index.init_index(max_elements=n, ef_construction=200, M=32)
    index.add_items(vectors, list(range(n)))
    # Higher ef = better recall at query time
    index.set_ef(max(50, hash_distance_similar * 10))

    if progress_cb:
        progress_cb(1, 3, "Building similarity index")

    if controller:
        controller.checkpoint()

    # Step 3: Query each point for neighbors within threshold
    # k = number of neighbors to retrieve per point.
    # We cap it to avoid excessive memory use but ensure good recall.
    k = min(n, 50)
    labels, distances = index.knn_query(vectors, k=k)

    if progress_cb:
        progress_cb(2, 3, "Grouping similar images")

    if controller:
        controller.checkpoint()

    # Step 4: Build edges from query results
    # L2 squared distance on binary {0,1} vectors equals hamming distance
    edges: dict[int, set[int]] = {row["id"]: set() for row in remaining}
    for i in range(n):
        img_id = id_list[i]
        for j in range(k):
            neighbor_idx = int(labels[i][j])
            if neighbor_idx == i:
                continue
            dist = int(round(distances[i][j]))
            if hash_distance_exact < dist <= hash_distance_similar:
                neighbor_id = id_list[neighbor_idx]
                edges[img_id].add(neighbor_id)
                edges[neighbor_id].add(img_id)

    if progress_cb:
        progress_cb(3, 3, "Grouping similar images")

    return _connected_components(edges)


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

    # Use HNSW for large sets, brute-force for small ones
    if len(remaining) >= _HNSW_MIN_SIZE:
        similar_groups = _find_similar_hnsw(
            remaining,
            hash_distance_exact,
            hash_distance_similar,
            progress_cb,
            controller,
        )
    else:
        similar_groups = _find_similar_bruteforce(
            remaining,
            hash_distance_exact,
            hash_distance_similar,
            progress_cb,
            controller,
        )

    return exact_groups, similar_groups
