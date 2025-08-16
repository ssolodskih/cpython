import functools, inspect
from typing import get_origin, get_args, Union

def __typed_def_validator__(fn):
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        for name, param in sig.parameters.items():
            if name not in bound.arguments:
                continue
            ann = param.annotation
            if ann is inspect._empty:
                continue
            val = bound.arguments[name]
            if not _check_type(ann, val):
                raise TypeError(
                    f"{fn.__name__}({name}=...) expected {ann!r}, got {type(val).__name__}"
                )
        return fn(*args, **kwargs)
    return wrapper

def _check_type(ann, val):
    origin = get_origin(ann)
    if origin is None:
        return isinstance(val, ann) if isinstance(ann, type) else True
    if origin is list or origin is set or origin is frozenset:
        (elem_type,) = get_args(ann)
        return isinstance(val, origin) and all(_check_type(elem_type, x) for x in val)
    if origin is tuple:
        args = get_args(ann)
        if len(args) == 2 and args[1] is Ellipsis:
            return isinstance(val, tuple) and all(_check_type(args[0], x) for x in val)
        return isinstance(val, tuple) and len(val) == len(args) and all(
            _check_type(a, x) for a, x in zip(args, val)
        )
    if origin is dict:
        k, v = get_args(ann)
        return isinstance(val, dict) and all(_check_type(k, kk) and _check_type(v, vv) for kk, vv in val.items())
    if origin is Union:
        return any(_check_type(a, val) for a in get_args(ann))
    return True  # don't block unknown annotations
