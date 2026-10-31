"""One top50-before-union expansion, with verified cached identity inference."""

import json
import numpy as np
from lightfm import LightFM
from .lightfm_features import PARAMETERS, predictive_hash


def restore_lightfm(path, expected_state_hash):
    mapping = json.loads((path / "mappings.json").read_text())
    model = LightFM(**PARAMETERS)
    # LightFM's prediction API checks optimizer buffers too. They are unused in
    # inference; all predictive arrays are overwritten before any score call.
    model._initialize(
        10, len(mapping["items_in_index_order"]), len(mapping["users_in_index_order"])
    )
    arrays = dict(np.load(path / "lightfm_predictive_arrays.npz"))
    for name, values in arrays.items():
        setattr(model, name, np.ascontiguousarray(values))
    assert predictive_hash(model) == expected_state_hash
    ubias, _ = model.get_user_representations()
    ibias, _ = model.get_item_representations()
    return {
        "model": model,
        "users": mapping["users_in_index_order"],
        "items": mapping["items_in_index_order"],
        "user_index": mapping["user_to_index"],
        "item_index": mapping["item_to_index"],
        "user_biases": ubias,
        "item_biases": ibias,
        "mappings": mapping,
    }


def expand_candidates(original, ranked_available, n50, supported_user):
    # Filter to unseen first, then truncate, THEN union. Never scan for 50 new IDs.
    selected = (
        [it for it in ranked_available if n50.get(it, 0) == 0][:50]
        if supported_user
        else []
    )
    return sorted(set(original) | set(selected)), selected


def lightfm_ranking(bundle, u, available):
    if u not in bundle["user_index"]:
        return []
    supported = sorted(set(available) & set(bundle["item_index"]))
    ids = np.asarray([bundle["item_index"][it] for it in supported], dtype=np.int32)
    if not len(ids):
        return []
    scores = bundle["model"].predict(bundle["user_index"][u], ids, num_threads=1)
    assert np.isfinite(scores).all()
    return [supported[j] for j in np.argsort(-scores, kind="stable")]
