"""Authentication module for XRM MCP.

Provides token acquisition for Dataverse/XRM via Azure CLI and MSAL fallback.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from msal import PublicClientApplication, SerializableTokenCache


def get_token(org_url: str) -> str:
    """Get an access token for the given Dataverse/XRM organization URL.

    Tries Azure CLI first, then falls back to MSAL device flow.

    Args:
        org_url: The organization URL (e.g., https://yourorg.crm4.dynamics.com)

    Returns:
        The access token string

    Raises:
        RuntimeError: If both authentication methods fail
    """
    # Strip trailing slash from org_url
    org_url = org_url.rstrip("/")

    # Try Azure CLI first
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", org_url],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            token_data = json.loads(result.stdout)
            return token_data["accessToken"]
    except (FileNotFoundError, subprocess.TimeoutExpired, KeyError, json.JSONDecodeError):
        # Azure CLI not available or failed, continue to MSAL
        pass

    # Try MSAL with device flow
    client_id = "51f81489-12ee-4a9e-aaae-a2591f45987d"
    authority = "https://login.microsoftonline.com/common"
    scope = [f"{org_url}/.default"]

    # Setup token cache
    cache_dir = Path.home() / ".xrm-mcp"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / "cache.json"

    cache = SerializableTokenCache()
    if cache_file.exists():
        cache.deserialize(cache_file.read_text())

    app = PublicClientApplication(
        client_id=client_id,
        authority=authority,
        token_cache=cache,
    )

    # Try silent token acquisition first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scope, account=accounts[0])
        if result and "access_token" in result:
            # Save cache
            if cache.has_state_changed:
                cache_file.write_text(cache.serialize())
            return result["access_token"]

    # Fall back to device flow
    flow = app.initiate_device_flow(scopes=scope)
    if "user_code" not in flow:
        raise RuntimeError(
            "Failed to initiate device flow authentication. "
            "Please ensure you have network connectivity."
        )

    # Print device flow message to stderr only
    print(flow["message"], file=sys.stderr)

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        # Save cache
        if cache.has_state_changed:
            cache_file.write_text(cache.serialize())
        return result["access_token"]

    # Both methods failed
    error_msg = result.get("error_description", result.get("error", "Unknown error"))
    raise RuntimeError(
        f"Failed to acquire token for {org_url}. "
        f"Azure CLI failed and MSAL device flow failed: {error_msg}"
    )


if __name__ == "__main__":
    """Standalone test: python -m xrm_mcp.auth https://yourorg.crm4.dynamics.com"""
    if len(sys.argv) != 2:
        print("Usage: python -m xrm_mcp.auth <org_url>", file=sys.stderr)
        sys.exit(1)

    try:
        token = get_token(sys.argv[1])
        print(f"Successfully acquired token (length: {len(token)})")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
