"""Tests that the server still builds and exposes its tools on the pinned FastMCP version.

These run entirely in-memory: no Dataverse environment or credentials are used.
"""

import asyncio

from fastmcp import Client

from xrm_mcp.server import _clean_record, mcp

EXPECTED_TOOLS = {
    "ping",
    "list_tables",
    "describe_table",
    "find_table",
    "query_records",
    "create_record",
    "update_record",
    "upsert_record",
}


def test_server_exposes_expected_tools():
    async def list_tools():
        async with Client(mcp) as client:
            return await client.list_tools()

    tools = asyncio.run(list_tools())
    assert {tool.name for tool in tools} == EXPECTED_TOOLS


def test_tool_schemas_are_generated():
    async def list_tools():
        async with Client(mcp) as client:
            return await client.list_tools()

    for tool in asyncio.run(list_tools()):
        assert tool.description
        assert tool.inputSchema["type"] == "object"
        assert "org_url" in tool.inputSchema["properties"]


def test_clean_record_uses_formatted_values_and_drops_annotations():
    record = {
        "@odata.etag": 'W/"123"',
        "na_name": "Example",
        "statuscode": 1,
        "statuscode@OData.Community.Display.V1.FormattedValue": "Active",
        "_na_project_value": "00000000-0000-0000-0000-000000000000",
        "_na_project_value@OData.Community.Display.V1.FormattedValue": "Project X",
    }

    assert _clean_record(record) == {
        "na_name": "Example",
        "statuscode": "Active",
        "na_project": "Project X",
    }
