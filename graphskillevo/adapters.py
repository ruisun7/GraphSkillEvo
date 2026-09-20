"""Environment adapter registry for the standalone graphskillevo entry."""
from __future__ import annotations

import inspect


_ENV_REGISTRY: dict[str, type] = {}


def register_builtins() -> None:
    """Lazy-import built-in GraphSkillEvo adapters."""
    try:
        from graphskillevo.envs.alfworld.adapter import ALFWorldAdapter

        _ENV_REGISTRY["alfworld"] = ALFWorldAdapter
    except ImportError:
        pass
    try:
        from graphskillevo.envs.searchqa.adapter import SearchQAAdapter

        _ENV_REGISTRY["searchqa"] = SearchQAAdapter
    except ImportError:
        pass
    try:
        from graphskillevo.envs.livemathematicianbench.adapter import LiveMathematicianBenchAdapter

        _ENV_REGISTRY["livemathematicianbench"] = LiveMathematicianBenchAdapter
    except ImportError:
        pass
    try:
        from graphskillevo.envs.spreadsheetbench.adapter import SpreadsheetBenchAdapter

        _ENV_REGISTRY["spreadsheetbench"] = SpreadsheetBenchAdapter
    except ImportError:
        pass
    try:
        from graphskillevo.envs.docvqa.adapter import DocVQAAdapter

        _ENV_REGISTRY["docvqa"] = DocVQAAdapter
    except ImportError:
        pass

def get_adapter(cfg: dict):
    register_builtins()
    env_name = cfg.get("env", "")
    if env_name not in _ENV_REGISTRY:
        raise ValueError(f"Unknown environment {env_name!r}. Available: {sorted(_ENV_REGISTRY)}")
    adapter_cls = _ENV_REGISTRY[env_name]
    sig = inspect.signature(adapter_cls.__init__)
    accepted = set(sig.parameters) - {"self"}
    kwargs = {key: cfg[key] for key in accepted if key in cfg}
    return adapter_cls(**kwargs)
