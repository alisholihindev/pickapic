from __future__ import annotations

import numpy as np
import hnswlib


def _phash_to_vec(phash_hex: str) -> np.ndarray:
    """Convert 16-char hex pHash to 64-bit uint8 vector."""
    val = int(phash_hex, 16)
    bits = np.array([(val >> i) & 1 for i in range(63, -1, -1)], dtype=np.float32)
    return bits


def find_hash_groups(
    records: list[dict],
    hash_distance_exact: int = 0,
    hash_distance_similar: int = 10,
) -> tuple[list[list[int]], list[list[int]]]:
    """
    records: [{id, phash}, ...]
    Returns (exact_groups, similar_groups) — each group is a list of image ids.
    Uses hnswlib with hamming-like L2 on bit vectors.
    """
    if len(records) < 2:
        return [], []

    ids = [r["id"] for r in records]
    vecs = np.stack([_phash_to_vec(r["phash"]) for r in records])

    n = len(ids)
    dim = 64
    index = hnswlib.Index(space="l2", dim=dim)
    index.init_index(max_elements=n, ef_construction=200, M=16)
    index.add_items(vecs, ids)
    index.set_ef(50)

    labels, distances = index.knn_query(vecs, k=min(10, n))

    visited = set()
    exact_groups: list[list[int]] = []
    similar_groups: list[list[int]] = []

    for i, (neighbors, dists) in enumerate(zip(labels, distances)):
        src_id = ids[i]
        if src_id in visited:
            continue
        exact = [src_id]
        similar = []
        for nb_id, dist in zip(neighbors, dists):
            if nb_id == src_id:
                continue
            if nb_id in visited:
                continue
            d = int(round(dist))
            if d <= hash_distance_exact:
                exact.append(nb_id)
            elif d <= hash_distance_similar:
                similar.append(nb_id)

        if len(exact) > 1:
            for eid in exact:
                visited.add(eid)
            exact_groups.append(exact)
        elif similar:
            group = [src_id] + similar
            for sid in group:
                visited.add(sid)
            similar_groups.append(group)

    return exact_groups, similar_groups


