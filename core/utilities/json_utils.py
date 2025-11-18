"""
JSON Utilities with orjson Optimization

Provides JSON loading/dumping functions with automatic fallback from orjson to standard json.
"""

import json
import logging
from typing import Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import orjson for better performance
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    logger.debug("orjson not available, using standard json")


def load_json(file_path: Union[str, Path]) -> Any:
    """
    Load JSON from file with orjson optimization.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Example:
        >>> data = load_json("model.json")
    """
    with open(file_path, 'rb') as f:
        if HAS_ORJSON:
            return orjson.loads(f.read())
        return json.load(f)


def loads_json(data: Union[bytes, str]) -> Any:
    """
    Parse JSON string/bytes with orjson optimization.

    Args:
        data: JSON string or bytes

    Returns:
        Parsed JSON data

    Example:
        >>> obj = loads_json('{"key": "value"}')
        >>> obj = loads_json(b'{"key": "value"}')
    """
    if HAS_ORJSON and isinstance(data, bytes):
        return orjson.loads(data)
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)


def dump_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Dump data to JSON file with orjson optimization.

    Args:
        data: Data to serialize
        file_path: Output file path
        indent: Indentation level (default: 2)

    Example:
        >>> dump_json({"key": "value"}, "output.json")
    """
    with open(file_path, 'wb' if HAS_ORJSON else 'w') as f:
        if HAS_ORJSON:
            # orjson option for pretty printing
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        else:
            json.dump(data, f, indent=indent)


def dumps_json(data: Any, indent: int = 2) -> str:
    """
    Serialize data to JSON string with orjson optimization.

    Args:
        data: Data to serialize
        indent: Indentation level (default: 2)

    Returns:
        JSON string

    Example:
        >>> json_str = dumps_json({"key": "value"})
    """
    if HAS_ORJSON:
        return orjson.dumps(data, option=orjson.OPT_INDENT_2).decode('utf-8')
    return json.dumps(data, indent=indent)
