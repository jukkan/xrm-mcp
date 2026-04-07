"""Schema discovery module for XRM MCP.

Provides table and column metadata from Dataverse.
"""

from typing import Any

from .api import fetch


def list_tables(org_url: str, token: str, search: str = "", custom_only: bool = True, prefix: str = "", exclude_ms_prefixes: bool = True) -> list[dict[str, Any]]:
    """List tables (entity definitions) in the Dataverse environment.

    Args:
        org_url: The organization URL
        token: The access token
        search: Optional search term to filter by logical name or display name
        custom_only: If True, only return custom entities (default: True)
        prefix: Optional prefix to filter logical names (e.g., "cr123_")
        exclude_ms_prefixes: If True, exclude Microsoft-prefixed solution tables (default: True)

    Returns:
        List of table metadata dictionaries with keys:
        - logical_name: The logical name (e.g., account, cr123_hourentry)
        - display_name: The display name
        - entity_set_name: The entity set name for Web API
        - is_custom: Whether this is a custom entity
        - description: The description (may be empty)
    """
    params = {
        "$select": "LogicalName,DisplayName,Description,EntitySetName,IsCustomEntity",
    }

    # Build server-side filter
    filters = []

    if custom_only:
        filters.append("IsCustomEntity eq true")

    if prefix:
        filters.append(f"startswith(LogicalName,'{prefix}')")

    # Add search filtering server-side when custom_only=True
    if search and custom_only:
        # Filter LogicalName server-side, DisplayName will be filtered client-side
        # Note: Complex DisplayName filtering with LocalizedLabels/any is not supported by Dataverse
        filters.append(f"contains(LogicalName,'{search}')")

    if filters:
        params["$filter"] = " and ".join(filters)

    response = fetch(org_url, "EntityDefinitions", token, params)
    tables = []

    # Microsoft-prefixed solution tables to exclude
    ms_prefixes = (
        "msdyn_", "msdynmkt_", "msdyncrm_", "msfp_", "adx_", "mspp_", "bot_",
        "botcomponent_", "flowmachine", "flowsession", "desktopflow",
        "workqueue", "gitbranch", "gitorganization", "gitrepository"
    )

    for entity in response.get("value", []):
        # Extract display name label
        display_name_labels = entity.get("DisplayName", {}).get("LocalizedLabels", [])
        display_name = display_name_labels[0].get("Label", "") if display_name_labels else ""

        # Extract description
        description_labels = entity.get("Description", {}).get("LocalizedLabels", [])
        description = description_labels[0].get("Label", "") if description_labels else ""

        logical_name = entity.get("LogicalName", "")

        # Filter out Microsoft-prefixed solution tables if requested
        # Note: prefix parameter overrides exclude_ms_prefixes
        if exclude_ms_prefixes and not prefix:
            if any(logical_name.startswith(p) for p in ms_prefixes):
                continue

        # Client-side filtering for search term
        if search:
            search_lower = search.lower()
            # If custom_only=True, LogicalName is already filtered server-side, only check DisplayName
            if custom_only:
                if search_lower not in display_name.lower():
                    # Already matched LogicalName server-side, check if also matches DisplayName
                    # If not, we still keep it because it matched LogicalName
                    pass
            else:
                # If custom_only=False, do full client-side filtering
                if search_lower not in logical_name.lower() and search_lower not in display_name.lower():
                    continue

        tables.append({
            "logical_name": logical_name,
            "display_name": display_name,
            "entity_set_name": entity.get("EntitySetName", ""),
            "is_custom": entity.get("IsCustomEntity", False),
            "description": description,
        })

    # Sort: custom entities first, then alphabetical by logical name
    tables.sort(key=lambda t: (not t["is_custom"], t["logical_name"]))

    return tables


def describe_table(org_url: str, token: str, table: str) -> dict[str, Any]:
    """Get column metadata for a specific table.

    Args:
        org_url: The organization URL
        token: The access token
        table: The logical name of the table

    Returns:
        Dictionary with keys:
        - table_name: The table logical name
        - columns: List of column metadata dictionaries with keys:
            - logical_name: The column logical name
            - display_name: The column display name
            - type: The attribute type
            - required: The required level (e.g., None, SystemRequired, ApplicationRequired)
            - description: The description (may be empty)
    """
    # Fetch attributes for the table
    path = f"EntityDefinitions(LogicalName='{table}')/Attributes"
    params = {
        "$select": "LogicalName,DisplayName,AttributeType,Description,RequiredLevel",
    }

    response = fetch(org_url, path, token, params)

    # Columns to exclude
    excluded_columns = {
        "versionnumber",
        "timezoneruleversionnumber",
        "utcconversiontimezonecode",
        "importsequencenumber",
        "overriddencreatedon",
    }

    columns = []
    for attr in response.get("value", []):
        logical_name = attr.get("LogicalName", "")

        # Skip excluded columns
        if logical_name in excluded_columns:
            continue

        # Extract display name label
        display_name_labels = attr.get("DisplayName", {}).get("LocalizedLabels", [])
        display_name = display_name_labels[0].get("Label", "") if display_name_labels else ""

        # Extract description
        description_labels = attr.get("Description", {}).get("LocalizedLabels", [])
        description = description_labels[0].get("Label", "") if description_labels else ""

        # Extract required level
        required_level = attr.get("RequiredLevel", {}).get("Value", "None")

        columns.append({
            "logical_name": logical_name,
            "display_name": display_name,
            "type": attr.get("AttributeType", ""),
            "required": required_level,
            "description": description,
        })

    return {
        "table_name": table,
        "columns": columns,
    }
