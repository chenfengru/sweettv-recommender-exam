"""Fixed sparse binary item-item model and direct-retrieval measurements."""

import math
from collections import defaultdict
import numpy as np
from scipy.sparse import csr_matrix


def sparse_bytes(matrix):
    return matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes


def fit_item_item(n50, *, top_k=50, shrinkage=20, min_coview=3, block_items=128):
    """Bound multiplication to one sparse source-item block at a time.

    Parameters are exposed for small hand-computable tests, not experiment search.
    Neighbour pruning precedes prediction-window availability filtering.
    """
    users = sorted(n50)
    items = sorted({it for c in n50.values() for it, n in c.items() if n > 0})
    item_index = {it: j for j, it in enumerate(items)}
    indices, indptr = [], [0]
    for u in users:
        indices.extend(sorted(item_index[it] for it, n in n50[u].items() if n > 0))
        indptr.append(len(indices))
    binary = csr_matrix(
        (
            np.ones(len(indices), dtype=np.int64),
            np.array(indices, dtype=np.int32),
            np.array(indptr, dtype=np.int32),
        ),
        shape=(len(users), len(items)),
    )
    support = np.asarray(binary.sum(axis=0)).ravel()
    transposed = binary.T.tocsr()
    neighbours = {}
    largest_block_bytes, largest_block_nnz, eligible_pairs = 0, 0, 0
    for start in range(0, len(items), block_items):
        coview = (transposed[start : start + block_items] @ binary).tocsr()
        largest_block_bytes = max(largest_block_bytes, sparse_bytes(coview))
        largest_block_nnz = max(largest_block_nnz, coview.nnz)
        for offset in range(coview.shape[0]):
            i = start + offset
            begin, end = coview.indptr[offset : offset + 2]
            scored = []
            for j, c in zip(coview.indices[begin:end], coview.data[begin:end]):
                if i == j or c < min_coview:
                    continue
                c = int(c)
                similarity = (
                    c
                    / math.sqrt(int(support[i]) * int(support[j]))
                    * c
                    / (c + shrinkage)
                )
                scored.append((int(j), similarity))
            eligible_pairs += len(scored)
            scored.sort(key=lambda pair: (-pair[1], items[pair[0]]))
            neighbours[items[i]] = [(items[j], score) for j, score in scored[:top_k]]
        del coview
    stats = {
        "training_users": len(users),
        "training_items": len(items),
        "binary_pairs": binary.nnz,
        "binary_dtype": str(binary.dtype),
        "binary_sparse_bytes": sparse_bytes(binary),
        "transpose_sparse_bytes": sparse_bytes(transposed),
        "max_coview_block_sparse_bytes": largest_block_bytes,
        "max_coview_block_nnz": largest_block_nnz,
        "eligible_directed_pairs_before_pruning": eligible_pairs,
        "retained_directed_neighbours": sum(map(len, neighbours.values())),
        "items_without_neighbours": sum(not v for v in neighbours.values()),
        "top_k": top_k,
        "shrinkage": shrinkage,
        "minimum_coview": min_coview,
        "block_items": block_items,
    }
    return neighbours, {it: int(support[j]) for j, it in enumerate(items)}, stats


def score_user(counts, neighbours, candidates):
    contributions = defaultdict(float)
    for source in sorted(counts):
        if counts[source] <= 0:
            continue
        weight = math.log1p(counts[source])
        for destination, similarity in neighbours.get(source, []):
            if destination in candidates:
                contributions[destination] += weight * similarity
    direct = sorted(contributions, key=lambda it: (-contributions[it], it))
    unseen = [it for it in direct if counts.get(it, 0) == 0]
    return direct, unseen


def recall_summary(targets, ranking, k):
    eligible = [u for u, t in targets.items() if t]
    hits = {u: len(set(ranking[u][:k]) & set(t)) for u, t in targets.items()}
    denominator = sum(len(t) for t in targets.values())
    return {
        "users": len(targets),
        "users_with_targets": len(eligible),
        "users_without_targets": len(targets) - len(eligible),
        "hits": sum(hits.values()),
        "target_items": denominator,
        "macro_conditional": (
            math.fsum(hits[u] / len(targets[u]) for u in eligible) / len(eligible)
            if eligible
            else None
        ),
        "macro_cohort_zero_for_no_targets": (
            math.fsum(hits[u] / len(targets[u]) for u in eligible) / len(targets)
            if targets
            else None
        ),
        "micro": sum(hits.values()) / denominator if denominator else None,
    }


def retrieval_metrics(truth, histories, direct, unseen):
    targets = {u: set(t) for u, t in truth.items()}
    absent = {u: t - set(histories.get(u, {})) for u, t in targets.items()}
    result = {}
    base_hits = sum(len(t & set(histories.get(u, {}))) for u, t in targets.items())
    base_macro = math.fsum(
        len(t & set(histories.get(u, {}))) / len(t) for u, t in targets.items()
    ) / len(targets)
    for k in (20, 50):
        covered = {
            u: t & (set(histories.get(u, {})) | set(unseen[u][:k]))
            for u, t in targets.items()
        }
        union_hits = sum(map(len, covered.values()))
        union_macro = math.fsum(
            len(covered[u]) / len(t) for u, t in targets.items()
        ) / len(targets)
        result[str(k)] = {
            "all_ranking_all_targets": recall_summary(targets, direct, k),
            "all_ranking_absent_targets": recall_summary(absent, direct, k),
            "unseen_ranking_absent_targets": recall_summary(absent, unseen, k),
            "union_with_personal_history": {
                "base_hits": base_hits,
                "union_hits": union_hits,
                "additional_relevant_items": union_hits - base_hits,
                "target_items": sum(map(len, targets.values())),
                "base_macro_coverage": base_macro,
                "union_macro_coverage": union_macro,
                "macro_coverage_gain": union_macro - base_macro,
                "base_micro_coverage": base_hits / sum(map(len, targets.values())),
                "union_micro_coverage": union_hits / sum(map(len, targets.values())),
                "micro_coverage_gain": (union_hits - base_hits)
                / sum(map(len, targets.values())),
                "union_personal_only_oracle_map_at_5": math.fsum(
                    min(5, len(covered[u])) / min(5, len(t)) for u, t in targets.items()
                )
                / len(targets),
                "users_with_extra_relevant_items": sum(
                    bool(set(unseen[u][:k]) & absent[u]) for u in targets
                ),
            },
        }
    return result
