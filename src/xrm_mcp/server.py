"""FastMCP server implementation for XRM MCP.

Provides 6 MCP tools for reading and writing Dataverse/XRM data.
"""

from typing import Any

from fastmcp import FastMCP

from . import schema as schema_module
from .api import fetch, patch, post
from .auth import get_token

# Initialize FastMCP server
mcp = FastMCP("xrm-mcp")


@mcp.tool()
def ping(org_url: str) -> dict[str, Any]:
    """Test connectivity to an XRM/Dataverse environment and verify authentication.

    Call this first to verify your setup and connection to the Dataverse environment.

    Args:
        org_url: The Dataverse organization URL (e.g., https://yourorg.crm4.dynamics.com)

    Returns:
        Dictionary with status, org_url, user_id, business_unit_id, org_id
    """
    token = get_token(org_url)
    response = fetch(org_url, "WhoAmI", token)

    return {
        "status": "ok",
        "org_url": org_url,
        "user_id": response.get("UserId", ""),
        "business_unit_id": response.get("BusinessUnitId", ""),
        "org_id": response.get("OrganizationId", ""),
    }


@mcp.tool()
def list_tables(org_url: str, search: str = "", custom_only: bool = True, prefix: str = "", exclude_ms_prefixes: bool = True) -> list[dict[str, Any]]:
    """Lists Dataverse tables. Defaults to custom tables only, excluding Microsoft-prefixed solution tables (msdyn_, msfp_, adx_ etc).

    Use prefix='na_' to filter to a specific publisher. Use exclude_ms_prefixes=False to see all custom tables.

    Args:
        org_url: The Dataverse organization URL (e.g., https://yourorg.crm4.dynamics.com)
        search: Optional search term to filter tables
        custom_only: If True, only return custom entities (default: True)
        prefix: Optional prefix to filter logical names (e.g., "cr123_")
        exclude_ms_prefixes: If True, exclude Microsoft-prefixed solution tables (default: True)

    Returns:
        List of tables with logical_name, display_name, entity_set_name, is_custom, description
    """
    token = get_token(org_url)
    return schema_module.list_tables(org_url, token, search, custom_only, prefix, exclude_ms_prefixes)


@mcp.tool()
def describe_table(org_url: str, table: str) -> dict[str, Any]:
    """Get columns, types and descriptions for an XRM table.

    Call this before querying when you need to know column names for $select or $filter.

    Args:
        org_url: The Dataverse organization URL
        table: The logical name of the table (e.g., account, cr123_hourentry)

    Returns:
        Dictionary with table_name and columns list containing metadata for each column
    """
    token = get_token(org_url)
    return schema_module.describe_table(org_url, token, table)


@mcp.tool()
def query_records(
    org_url: str,
    table: str,
    select: str = "",
    filter: str = "",
    top: int = 100,
    orderby: str = "",
) -> dict[str, Any]:
    """Query records from an XRM/Dataverse table.

    Args:
        org_url: The Dataverse organization URL
        table: The logical name (e.g., account, cr123_hourentry)
        select: Comma-separated column names to retrieve
        filter: OData $filter expression
        top: Maximum records to return (hard cap 5000)
        orderby: OData $orderby expression

    Returns:
        Dictionary with count and records list
    """
    token = get_token(org_url)

    # Get entity set name from table metadata
    table_info = schema_module.describe_table(org_url, token, table)

    # Need to fetch entity set name separately
    entity_params = {
        "$select": "EntitySetName",
        "$filter": f"LogicalName eq '{table}'",
    }
    entity_response = fetch(org_url, "EntityDefinitions", token, entity_params)
    entity_set_name = entity_response.get("value", [{}])[0].get("EntitySetName", table + "s")

    # Build query parameters
    params: dict[str, Any] = {}

    if select:
        params["$select"] = select
    if filter:
        params["$filter"] = filter
    if top:
        # Enforce hard cap of 5000
        params["$top"] = min(top, 5000)
    if orderby:
        params["$orderby"] = orderby

    # Query the records
    response = fetch(org_url, entity_set_name, token, params)

    records = response.get("value", [])

    return {
        "count": len(records),
        "records": records,
    }


@mcp.tool()
def create_record(org_url: str, table: str, data: dict[str, Any]) -> dict[str, str]:
    """Create a single record in an XRM table.

    Args:
        org_url: The Dataverse organization URL
        table: The logical name of the table
        data: Dictionary of logical column names to values

    Returns:
        Dictionary with the created record id
    """
    token = get_token(org_url)

    # Get entity set name
    entity_params = {
        "$select": "EntitySetName",
        "$filter": f"LogicalName eq '{table}'",
    }
    entity_response = fetch(org_url, "EntityDefinitions", token, entity_params)
    entity_set_name = entity_response.get("value", [{}])[0].get("EntitySetName", table + "s")

    # Create the record
    response = post(org_url, entity_set_name, token, data)

    # Extract the ID from the response
    if "id" in response:
        return {"id": response["id"]}

    # Try to extract from the primary key field (usually {table}id)
    primary_key = f"{table}id"
    if primary_key in response:
        return {"id": response[primary_key]}

    # Return the full response if we can't find the ID
    return response


@mcp.tool()
def update_record(org_url: str, table: str, record_id: str, data: dict[str, Any]) -> dict[str, str]:
    """Update fields on a single existing XRM record.

    Args:
        org_url: The Dataverse organization URL
        table: The logical name of the table
        record_id: The GUID of the record to update
        data: Dictionary of fields to change (only the fields to update)

    Returns:
        Success confirmation
    """
    token = get_token(org_url)

    # Get entity set name
    entity_params = {
        "$select": "EntitySetName",
        "$filter": f"LogicalName eq '{table}'",
    }
    entity_response = fetch(org_url, "EntityDefinitions", token, entity_params)
    entity_set_name = entity_response.get("value", [{}])[0].get("EntitySetName", table + "s")

    # Update the record
    path = f"{entity_set_name}({record_id})"
    patch(org_url, path, token, data)

    return {"success": True, "id": record_id}


@mcp.tool()
def upsert_record(
    org_url: str,
    table: str,
    alternate_key: str,
    alternate_value: str,
    data: dict[str, Any],
) -> dict[str, str]:
    """Create or update a record matched by an alternate key column.

    Use this for sync/import scenarios where you don't have the record GUID.

    Args:
        org_url: The Dataverse organization URL
        table: The logical name of the table
        alternate_key: The logical name of the alternate key column
        alternate_value: The value to match
        data: Dictionary of fields to set

    Returns:
        Success confirmation
    """
    token = get_token(org_url)

    # Get entity set name
    entity_params = {
        "$select": "EntitySetName",
        "$filter": f"LogicalName eq '{table}'",
    }
    entity_response = fetch(org_url, "EntityDefinitions", token, entity_params)
    entity_set_name = entity_response.get("value", [{}])[0].get("EntitySetName", table + "s")

    # Upsert using alternate key
    path = f"{entity_set_name}({alternate_key}='{alternate_value}')"
    patch(org_url, path, token, data, if_match="*", if_none_match="*")

    return {"success": True, "alternate_key": alternate_key, "alternate_value": alternate_value}


def main():
    """Entry point for the xrm-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
