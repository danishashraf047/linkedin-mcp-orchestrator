import asyncio
import json
from pathlib import Path
from typing import Any

from app.config import get_settings


class ContentMemory:
    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self.path = path or settings.content_history_path
        self._lock = asyncio.Lock()

    async def load(self) -> dict[str, Any]:
        async with self._lock:
            if not self.path.exists():
                return {"openings": [], "ctas": [], "formats": [], "styles": [], "fingerprints": []}
            return json.loads(self.path.read_text(encoding="utf-8"))

    async def append(self, record: dict[str, Any]) -> None:
        async with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {"openings": [], "ctas": [], "formats": [], "styles": [], "fingerprints": []}
            if self.path.exists():
                data.update(json.loads(self.path.read_text(encoding="utf-8")))
            for key, value in record.items():
                if key not in data:
                    data[key] = []
                data[key].append(value)
                data[key] = data[key][-100:]
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
