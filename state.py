"""Local state for the last branch tip observed by the monitor."""

import json
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class StateStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self, repository_key: str) -> Optional[str]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("Could not read saved state from %s: %s", self.path, error)
            return None
        if not isinstance(payload, dict) or payload.get("repository") != repository_key:
            return None
        sha = payload.get("sha")
        return sha if isinstance(sha, str) and sha else None

    def save(self, repository_key: str, sha: str) -> None:
        temporary_path = self.path.with_suffix(".tmp")
        payload = {"repository": repository_key, "sha": sha}
        temporary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary_path.replace(self.path)
