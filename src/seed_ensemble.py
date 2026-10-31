"""Predictive-tree identity and diversity helpers, independent of seed metadata."""

import hashlib
import json
import numpy as np


def predictive_tree_hash(model):
    def node(n):
        if "leaf_value" in n:
            return {"leaf_value": n["leaf_value"]}
        return {
            k: (node(n[k]) if k in ["left_child", "right_child"] else n[k])
            for k in [
                "split_feature",
                "threshold",
                "decision_type",
                "default_left",
                "missing_type",
                "left_child",
                "right_child",
            ]
        }

    dump = model.dump_model()
    payload = {
        "feature_names": dump["feature_names"],
        "num_tree_per_iteration": dump["num_tree_per_iteration"],
        "objective": dump["objective"],
        "trees": [node(t["tree_structure"]) for t in dump["tree_info"]],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def vector_diversity(values, reference):
    a = np.asarray(values)
    b = np.asarray(reference)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Aligned finite candidate vectors required.")
    delta = a - b
    return {
        "candidate_rows": len(a),
        "bitwise_identical": bool(np.array_equal(a, b)),
        "different_scores": int(np.sum(a != b)),
        "max_abs_difference": float(np.max(abs(delta))),
        "mean_abs_difference": float(np.mean(abs(delta))),
        "correlation": (
            float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else None
        ),
    }


def equal_score_mean(scores):
    if len(scores) != 4:
        raise ValueError("Exactly four fixed seeds required.")
    arrays = [np.asarray(x) for x in scores]
    if any(a.shape != arrays[0].shape or not np.isfinite(a).all() for a in arrays):
        raise ValueError("Aligned finite scores required.")
    return np.mean(np.stack(arrays), axis=0)
