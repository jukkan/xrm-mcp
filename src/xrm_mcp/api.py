"""API client module for XRM MCP.

Provides HTTP operations for the Dataverse Web API v9.2.
"""

from typing import Any

import httpx


def fetch(org_url: str, path: str, token: str, params: dict[str, Any] | None = None) -> dict:
    """Fetch data from the Dataverse Web API with automatic pagination.

    Args:
        org_url: The organization URL (e.g., https://yourorg.crm4.dynamics.com)
        path: The API path (e.g., EntityDefinitions or accounts)
        token: The access token
        params: Optional query parameters

    Returns:
        Response JSON with combined results if pagination is used

    Raises:
        httpx.HTTPStatusError: On non-2xx responses
    """
    org_url = org_url.rstrip("/")
    base_url = f"{org_url}/api/data/v9.2"
    url = f"{base_url}/{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Prefer": "odata.include-annotations=\"OData.Community.Display.V1.FormattedValue\"",
    }

    if params is None:
        params = {}

    all_values = []

    with httpx.Client(timeout=30.0) as client:
        while url:
            response = client.get(url, headers=headers, params=params if url.startswith(base_url) else None)
            response.raise_for_status()

            data = response.json()

            # Collect values if this is a collection response
            if "value" in data:
                all_values.extend(data["value"])

            # Check for next page
            next_link = data.get("@odata.nextLink")
            if next_link:
                url = next_link
                # Don't send params again on pagination links (they're in the URL)
                params = None
            else:
                # No more pages
                break

    # Return combined results if we have a collection
    if all_values:
        return {"value": all_values}

    # Return the single response for non-collection calls
    return data


def post(org_url: str, path: str, token: str, data: dict[str, Any]) -> dict:
    """Create a record via POST.

    Args:
        org_url: The organization URL
        path: The API path (entity set name)
        token: The access token
        data: The record data to create

    Returns:
        Response headers and data

    Raises:
        httpx.HTTPStatusError: On non-2xx responses
    """
    org_url = org_url.rstrip("/")
    url = f"{org_url}/api/data/v9.2/{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=data)
        response.raise_for_status()

        # Return the created record if available, otherwise extract ID from header
        if response.content:
            return response.json()

        # Extract ID from OData-EntityId header
        entity_id = response.headers.get("OData-EntityId", "")
        if entity_id:
            # Extract GUID from the URL
            record_id = entity_id.split("(")[-1].rstrip(")")
            return {"id": record_id}

        return {}


def patch(
    org_url: str,
    path: str,
    token: str,
    data: dict[str, Any],
    if_match: str | None = None,
    if_none_match: str | None = None,
) -> dict:
    """Update a record via PATCH.

    Args:
        org_url: The organization URL
        path: The API path including record ID
        token: The access token
        data: The fields to update
        if_match: Optional If-Match header for conditional update
        if_none_match: Optional If-None-Match header for upsert

    Returns:
        Response data (may be empty on success)

    Raises:
        httpx.HTTPStatusError: On non-2xx responses
    """
    org_url = org_url.rstrip("/")
    url = f"{org_url}/api/data/v9.2/{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if if_match:
        headers["If-Match"] = if_match
    if if_none_match:
        headers["If-None-Match"] = if_none_match

    with httpx.Client(timeout=30.0) as client:
        response = client.patch(url, headers=headers, json=data)
        response.raise_for_status()

        if response.content:
            return response.json()

        return {}
