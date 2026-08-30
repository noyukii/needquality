import json
from pathlib import Path
from typing import Any


def load_config(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text())
        return data.get("app", {})
    except Exception:
        return {}
