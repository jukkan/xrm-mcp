"""Authentication module for XRM MCP.

Provides token acquisition for Dataverse/XRM via Azure CLI and MSAL fallback,
preferring a per-org_url cached identity when one is known to work.
"""

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from msal import PublicClientApplication, SerializableTokenCache

from . import identity_cache

# Azure CLI writes a per-invocation telemetry log under ~/.azure/commands on
# every call. In sandboxed shells where ~/.azure isn't writable, this can make
# `az` calls fail even though the credential lookup itself would have worked.
# Disabling telemetry collection skips that write.
_AZ_CLI_ENV = {**os.environ, "AZURE_CORE_COLLECT_TELEMETRY": "false"}


def _decode_jwt_claims(token: str) -> dict[str, Any]:
    """Decode the payload of a JWT without verifying its signature.

    Used only to read the `tid` (tenant id) claim for identity bookkeeping.
    """
    try:
        payload_segment = token.split(".")[1]
        padding = "=" * (-len(payload_segment) % 4)
        decoded = base64.urlsafe_b64decode(payload_segment + padding)
        return json.loads(decoded)
    except (IndexError, ValueError, json.JSONDecodeError):
        return {}


def _try_azure_cli(org_url: str, tenant_id: str | None = None) -> str | None:
    """Attempt to get a token via Azure CLI, optionally for a specific tenant.

    Returns the access token, or None if the attempt failed.
    """
    cmd = ["az", "account", "get-access-token", "--resource", org_url, "--only-show-errors"]
    if tenant_id:
        cmd += ["--tenant", tenant_id]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, env=_AZ_CLI_ENV)
        if result.returncode == 0:
            token_data = json.loads(result.stdout)
            return token_data["accessToken"]
    except (FileNotFoundError, subprocess.TimeoutExpired, KeyError, json.JSONDecodeError):
        pass
    return None


def _load_msal_app() -> tuple[PublicClientApplication, SerializableTokenCache, Path]:
    client_id = "51f81489-12ee-4a9e-aaae-a2591f45987d"
    authority = "https://login.microsoftonline.com/common"

    cache_dir = Path.home() / ".xrm-mcp"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / "cache.json"

    cache = SerializableTokenCache()
    if cache_file.exists():
        cache.deserialize(cache_file.read_text())

    app = PublicClientApplication(client_id=client_id, authority=authority, token_cache=cache)
    return app, cache, cache_file


def _try_msal_silent(org_url: str, account_id: str | None = None) -> tuple[str | None, str | None]:
    """Attempt silent MSAL token acquisition.

    If account_id is given, only try that specific account. Otherwise try
    every cached account. Returns (token, account_id_used) or (None, None).
    """
    app, cache, cache_file = _load_msal_app()
    scope = [f"{org_url}/.default"]

    accounts = app.get_accounts()
    if account_id:
        accounts = [a for a in accounts if a.get("home_account_id") == account_id]

    for account in accounts:
        result = app.acquire_token_silent(scope, account=account)
        if result and "access_token" in result:
            if cache.has_state_changed:
                cache_file.write_text(cache.serialize())
            return result["access_token"], account.get("home_account_id")

    return None, None


def _device_flow(org_url: str) -> tuple[str, str | None]:
    app, cache, cache_file = _load_msal_app()
    scope = [f"{org_url}/.default"]

    flow = app.initiate_device_flow(scopes=scope)
    if "user_code" not in flow:
        raise RuntimeError(
            "Failed to initiate device flow authentication. "
            "Please ensure you have network connectivity."
        )

    print(flow["message"], file=sys.stderr)

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        if cache.has_state_changed:
            cache_file.write_text(cache.serialize())
        accounts = app.get_accounts()
        account_id = accounts[0].get("home_account_id") if accounts else None
        return result["access_token"], account_id

    error_msg = result.get("error_description", result.get("error", "Unknown error"))
    raise RuntimeError(f"Failed to acquire token for {org_url}: {error_msg}")


def get_token(org_url: str) -> tuple[str, dict[str, Any]]:
    """Get an access token for the given Dataverse/XRM organization URL.

    Prefers the identity that last succeeded for this org_url (cached by the
    caller after a verified successful API call). Falls back to Azure CLI's
    default identity, then any cached MSAL account, then MSAL device flow.

    Args:
        org_url: The organization URL (e.g., https://yourorg.crm4.dynamics.com)

    Returns:
        Tuple of (access_token, identity) where identity is
        {"method": "azcli"|"msal", "tenant_id": str|None, "account_id": str|None}

    Raises:
        RuntimeError: If all authentication methods fail
    """
    org_url = org_url.rstrip("/")

    cached = identity_cache.get(org_url)
    if cached:
        if cached.get("method") == "azcli":
            token = _try_azure_cli(org_url, tenant_id=cached.get("tenant_id"))
            if token:
                claims = _decode_jwt_claims(token)
                return token, {"method": "azcli", "tenant_id": claims.get("tid"), "account_id": None}
        elif cached.get("method") == "msal":
            token, account_id = _try_msal_silent(org_url, account_id=cached.get("account_id"))
            if token:
                claims = _decode_jwt_claims(token)
                return token, {"method": "msal", "tenant_id": claims.get("tid"), "account_id": account_id}
        # Cached identity didn't work — fall through to full discovery.

    # Full discovery: default Azure CLI identity first.
    token = _try_azure_cli(org_url)
    if token:
        claims = _decode_jwt_claims(token)
        return token, {"method": "azcli", "tenant_id": claims.get("tid"), "account_id": None}

    # Any cached MSAL account.
    token, account_id = _try_msal_silent(org_url)
    if token:
        claims = _decode_jwt_claims(token)
        return token, {"method": "msal", "tenant_id": claims.get("tid"), "account_id": account_id}

    # Device flow as last resort.
    token, account_id = _device_flow(org_url)
    claims = _decode_jwt_claims(token)
    return token, {"method": "msal", "tenant_id": claims.get("tid"), "account_id": account_id}


if __name__ == "__main__":
    """Standalone test: python -m xrm_mcp.auth https://yourorg.crm4.dynamics.com"""
    if len(sys.argv) != 2:
        print("Usage: python -m xrm_mcp.auth <org_url>", file=sys.stderr)
        sys.exit(1)

    try:
        token, identity = get_token(sys.argv[1])
        print(f"Successfully acquired token (length: {len(token)}), identity: {identity}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
