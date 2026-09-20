"""Helpers for locating local ALFWorld data payloads."""
from __future__ import annotations

import os


_GAME_SPLITS = ("train", "valid_seen", "valid_unseen")


def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def _normalize_data_root(path: str) -> str:
    expanded = os.path.abspath(os.path.expanduser(os.path.expandvars(str(path or "").strip())))
    if not expanded:
        return ""
    if os.path.basename(expanded) == "json_2.1.1":
        return os.path.dirname(expanded)
    return expanded


def iter_data_root_candidates() -> list[str]:
    """Return possible ALFWorld data roots in priority order."""
    candidates: list[str] = []

    env_root = _normalize_data_root(os.environ.get("ALFWORLD_DATA", ""))
    if env_root:
        candidates.append(env_root)

    bundled_root = os.path.join(_repo_root(), "data", "alfworld_data")
    if bundled_root not in candidates:
        candidates.append(bundled_root)

    return candidates


def resolve_data_root(required: bool = True) -> str:
    """Resolve the directory containing ``json_2.1.1/`` for ALFWorld."""
    for candidate in iter_data_root_candidates():
        if os.path.isdir(os.path.join(candidate, "json_2.1.1")):
            return candidate

    if not required:
        return ""

    current = os.environ.get("ALFWORLD_DATA", "").strip() or "<unset>"
    raise FileNotFoundError(
        "ALFWorld data root not found. Set ALFWORLD_DATA to the directory "
        "containing json_2.1.1/, logic/, and detectors/ "
        f"(current ALFWORLD_DATA={current})."
    )


def ensure_data_root_env() -> str:
    """Populate ``ALFWORLD_DATA`` when a valid local root can be inferred."""
    root = resolve_data_root(required=True)
    os.environ["ALFWORLD_DATA"] = root
    return root


def resolve_gamefile_path(gamefile: str, data_root: str | None = None) -> str:
    """Resolve a manifest gamefile entry to a local absolute path."""
    raw = str(gamefile or "").strip()
    if not raw:
        return ""

    expanded = os.path.expanduser(os.path.expandvars(raw))
    if os.path.isabs(expanded):
        return os.path.abspath(expanded)

    if os.path.exists(expanded):
        return os.path.abspath(expanded)

    root = _normalize_data_root(data_root or "") or resolve_data_root(required=False)
    if not root:
        return os.path.abspath(expanded)

    normalized = expanded.replace("\\", "/").lstrip("./")
    candidates: list[str] = []
    if normalized.startswith("json_2.1.1/"):
        candidates.append(os.path.join(root, normalized))
    elif normalized.startswith(_GAME_SPLITS):
        candidates.append(os.path.join(root, "json_2.1.1", normalized))
    else:
        candidates.append(os.path.join(root, normalized))
        candidates.append(os.path.join(root, "json_2.1.1", normalized))

    for candidate in candidates:
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    return os.path.abspath(candidates[0])
