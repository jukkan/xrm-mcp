"""Per-org_url identity cache for XRM MCP.

Remembers which auth identity (Azure CLI tenant or MSAL account) last
succeeded against a given Dataverse organization, so that switching between
multiple tenants (personal prod, demo environments, customer tenants) does
not require the default `az` login to always be the right one.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_CACHE_FILE = Path.home() / ".xrm-mcp" / "identity_cache.json"


def _normalize(org_url: str) -> str:
    return org_url.rstrip("/").lower()


def _load() -> dict[str, Any]:
    if not _CACHE_FILE.exists():
        return {}
    try:
        return json.loads(_CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict[str, Any]) -> None:
    _CACHE_FILE.parent.mkdir(exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(data, indent=2))


def get(org_url: str) -> dict[str, Any] | None:
    """Return the cached identity for org_url, or None if none is cached."""
    return _load().get(_normalize(org_url))


def set(
    org_url: str,
    method: str,
    tenant_id: str | None = None,
    account_id: str | None = None,
) -> None:
    """Record the identity that successfully worked for org_url."""
    data = _load()
    data[_normalize(org_url)] = {
        "method": method,
        "tenant_id": tenant_id,
        "account_id": account_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save(data)


def clear(org_url: str) -> None:
    """Remove the cached identity for org_url, forcing full discovery next time."""
    data = _load()
    key = _normalize(org_url)
    if key in data:
        del data[key]
        _save(data)
