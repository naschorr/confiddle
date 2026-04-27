from typing import Annotated, Union, get_args, get_origin

from pydantic import BaseModel


def unwrap_annotation(annotation):
    """
    Strip Optional[X] -> X and Annotated[X, ...] -> X, recursively.
    """
    origin = get_origin(annotation)
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        return unwrap_annotation(args[0]) if args else annotation
    if origin is Annotated:
        return unwrap_annotation(get_args(annotation)[0])
    return annotation


def is_container_annotation(annotation) -> bool:
    """
    Return True if the annotation represents a type that env var paths should descend into (a BaseModel subclass or
    dict), rather than assign a flat string value to.
    """
    inner = unwrap_annotation(annotation)
    # Unwrap parameterised forms like dict[str, Any] -> dict
    origin = get_origin(inner)
    if origin is not None:
        inner = origin
    try:
        return inner is dict or (isinstance(inner, type) and issubclass(inner, (BaseModel, dict)))
    except TypeError:
        return False


def get_field_annotation(model, key: str):
    """
    Return the annotation for field `key` on a BaseModel class, or None if not found.
    """
    if not (isinstance(model, type) and issubclass(model, BaseModel)):
        return None
    field_info = model.model_fields.get(key)
    return field_info.annotation if field_info else None
