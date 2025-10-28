from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List


@dataclass
class ErrorResponse:
    success: bool = False
    error: str = ""
    error_type: str = "unexpected_error"
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        # Only include keys with truthy values (keep success always present)
        data = asdict(self)
        out = {k: v for k, v in data.items() if (k == 'success' or v)}
        return out
