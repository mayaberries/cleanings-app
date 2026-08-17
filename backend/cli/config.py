"""
Where the CLI keeps its local state: the backend base URL it's pointed at,
and the JWT it got back from /users/login/token.

A plain JSON file under ~/.config, not the OS keyring -- this token is a
superuser's session token with a one-week default expiry (same as any
other user's), not a long-lived secret, and keeping it dependency-free
(no `keyring` package, which has flaky backends on headless Linux) matters
more here than marginally better local storage.
"""
import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "pets-admin-cli"
CONFIG_FILE = CONFIG_DIR / "credentials.json"
DEFAULT_API_BASE_URL = "http://localhost:8000/api"


def save_session(*, api_base_url: str, token: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_base_url": api_base_url, "token": token}, indent=2))
    CONFIG_FILE.chmod(0o600)


def load_session() -> Optional[dict]:
    if not CONFIG_FILE.exists():
        return None
    return json.loads(CONFIG_FILE.read_text())


def clear_session() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
