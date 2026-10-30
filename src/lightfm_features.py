"""Identity-only, support-aware WARP features with stable raw-ID mappings."""

import hashlib
import json
import time
import numpy as np
from scipy.sparse import csr_matrix
from lightfm import LightFM
from .schedule_features import EXTENDED_FEATURES, distribution

LIGHTFM_FEATURES = [
    "lightfm_score",
    "lightfm_rank",
    "lightfm_user_bias",
    "lightfm_item_bias",
    "lightfm_unsupported_user",
    "lightfm_unsupported_item",
]
FULL_FEATURES = EXTENDED_FEATURES + LIGHTFM_FEATURES
PARAMETERS = {
    "loss": "warp",
    "no_components": 10,
    "learning_rate": 0.05,
    "item_alpha": 0.0,
    "user_alpha": 0.0,
    "max_sampled": 10,
    "random_state": 42,
}


def binary_interactions(n50):
    users = sorted(u for u, c in n50.items() if any(n > 0 for n in c.values()))
    items = sorted({it for u in users for it, n in n50[u].items() if n > 0})
    ui = {u: i for i, u in enumerate(users)}
    ii = {it: i for i, it in enumerate(items)}
    indices = []
    indptr = [0]
    for u in users:
        indices.extend(sorted(ii[it] for it, n in n50[u].items() if n > 0))
        indptr.append(len(indices))
    matrix = csr_matrix(
        (
            np.ones(len(indices), dtype=np.float32),
            np.asarray(indices, dtype=np.int32),
            np.asarray(indptr, dtype=np.int32),
        ),
        shape=(len(users), len(items)),
    )
    if not matrix.nnz:
        raise ValueError("No positive N50 support for LightFM")
    return matrix, users, items, ui, ii


def predictive_hash(model):
    digest = hashlib.sha256()
    for name in ["user_embeddings", "item_embeddings", "user_biases", "item_biases"]:
        values = np.ascontiguousarray(getattr(model, name))
        digest.update(name.encode())
        digest.update(str((values.dtype.str, values.shape)).encode())
        digest.update(values.tobytes())
    return digest.hexdigest()


def fit_lightfm(n50):
    began = time.perf_counter()
    matrix, users, items, ui, ii = binary_interactions(n50)
    model = LightFM(**PARAMETERS)
    model.fit(matrix.tocoo(), epochs=15, num_threads=1, verbose=False)
    ubias, _ = model.get_user_representations()
    ibias, _ = model.get_item_representations()
    assert all(
        np.isfinite(getattr(model, key)).all()
        for key in ["user_embeddings", "item_embeddings", "user_biases", "item_biases"]
    )
    mappings = {
        "users_in_index_order": users,
        "items_in_index_order": items,
        "user_to_index": ui,
        "item_to_index": ii,
    }
    mapping_text = json.dumps(mappings, sort_keys=True, separators=(",", ":"))
    actual = model.get_params().copy()
    rng = actual.pop("random_state")
    state = rng.get_state()
    actual["random_state"] = {
        "type": type(rng).__name__,
        "initial_seed": 42,
        "fitted_state_sha256": hashlib.sha256(
            state[1].tobytes() + str(state[2:]).encode()
        ).hexdigest(),
    }
    report = {
        "supported_training_users": len(users),
        "supported_training_items": len(items),
        "binary_n50_pairs": matrix.nnz,
        "binary_dtype": str(matrix.dtype),
        "binary_matrix_bytes": matrix.data.nbytes
        + matrix.indices.nbytes
        + matrix.indptr.nbytes,
        "binary_sha256": hashlib.sha256(
            matrix.indptr.tobytes() + matrix.indices.tobytes() + matrix.data.tobytes()
        ).hexdigest(),
        "mapping_sha256": hashlib.sha256(mapping_text.encode()).hexdigest(),
        "predictive_state_sha256": predictive_hash(model),
        "requested_parameters": PARAMETERS,
        "actual_parameters": actual,
        "epochs": 15,
        "num_threads": 1,
        "identity_only": True,
        "fit_seconds": time.perf_counter() - began,
    }
    return {
        "model": model,
        "users": users,
        "items": items,
        "user_index": ui,
        "item_index": ii,
        "user_biases": ubias,
        "item_biases": ibias,
        "mappings": mappings,
        "report": report,
    }


def pair_features(bundle, users, candidate_items, available):
    ui, ii = bundle["user_index"], bundle["item_index"]
    supported_available = sorted(set(available) & set(ii))
    available_indices = np.asarray(
        [ii[it] for it in supported_available], dtype=np.int32
    )
    rows = []
    supported_users = 0
    for u, items in zip(users, candidate_items):
        known_user = u in ui
        supported_users += known_user
        score = {}
        ranks = {}
        if known_user and len(available_indices):
            values = bundle["model"].predict(ui[u], available_indices, num_threads=1)
            if not np.isfinite(values).all():
                raise ValueError("Non-finite LightFM score")
            score = dict(zip(supported_available, values))
            # Initial IDs are raw-string sorted; stable sort resolves exact score ties.
            order = np.argsort(-values, kind="stable")
            ranks = {supported_available[j]: rank for rank, j in enumerate(order, 1)}
        user_bias = float(bundle["user_biases"][ui[u]]) if known_user else 0
        for item in items:
            assert item in available
            known_item = item in ii
            item_bias = float(bundle["item_biases"][ii[item]]) if known_item else 0
            pair = known_user and known_item
            rows.append(
                [
                    float(score[item]) if pair else 0,
                    ranks[item] if pair else 0,
                    user_bias,
                    item_bias,
                    int(not known_user),
                    int(not known_item),
                ]
            )
    matrix = np.asarray(rows, dtype=np.float32).reshape(-1, 6)
    if not np.isfinite(matrix).all():
        raise ValueError("Non-finite LightFM feature")
    unsupported_pair = (matrix[:, 4] > 0) | (matrix[:, 5] > 0)
    assert np.all(matrix[unsupported_pair, :2] == 0) and np.all(
        matrix[~unsupported_pair, 1] >= 1
    )
    assert np.all(matrix[matrix[:, 4] > 0, 2] == 0) and np.all(
        matrix[matrix[:, 5] > 0, 3] == 0
    )
    report = {
        "available_programmes": len(available),
        "supported_available_programmes": len(supported_available),
        "available_item_support_fraction": len(supported_available) / len(available),
        "query_users": len(users),
        "supported_query_users": supported_users,
        "unsupported_query_users": len(users) - supported_users,
        "candidate_rows": len(matrix),
        "supported_pairs": int(np.sum(~unsupported_pair)),
        "unsupported_pairs": int(np.sum(unsupported_pair)),
        "unsupported_user_rows": int(np.sum(matrix[:, 4] > 0)),
        "unsupported_item_rows": int(np.sum(matrix[:, 5] > 0)),
        "unsupported_both_rows": int(np.sum((matrix[:, 4] > 0) & (matrix[:, 5] > 0))),
        "all_finite": True,
        "actual_missing_values": 0,
        "score_rank_zero_for_unsupported_pairs": True,
        "rank_scope": "ALL available origin-supported programmes, including repeats; one-based, raw-string ID exact ties.",
        "feature_sha256": hashlib.sha256(matrix.tobytes()).hexdigest(),
        "distributions": distribution(matrix, LIGHTFM_FEATURES),
    }
    return matrix, report


def append_features(base, additions):
    if base.ndim != 2 or base.shape[1] != 34 or additions.shape != (len(base), 6):
        raise ValueError("LightFM feature alignment mismatch")
    matrix = np.concatenate([base, additions], axis=1)
    assert (
        matrix.shape[1] == 40
        and np.isfinite(matrix).all()
        and np.array_equal(matrix[:, :34], base)
    )
    return matrix
