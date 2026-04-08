# XRM MCP Skill

## When to use xrm-mcp (not dv-python-sdk, not PAC CLI)
- User asks to query, list, find, describe, or summarize Dataverse data
- User mentions a table by display name ("hour entries", "deals")
- User wants records from a date range, filtered by status or owner
- User wants to know what tables exist in an environment
- User wants to check connectivity to an environment

## Preferred workflow for any Dataverse data request

1. ping(org_url) — confirm connectivity if environment is new this session
2. find_table(org_url, "friendly name") — resolve display name to logical name
3. describe_table(org_url, logical_name) — get exact column names
4. query_records(org_url, table, select, filter, orderby, top) — get data

Skip steps you already have answers for. If you ran list_tables or
describe_table earlier in the session, reuse those results.

## Routing rules
- "preferred" means: use xrm-mcp before considering any other path
- If xrm-mcp returns an error, surface it to the user — do not silently
  fall back to dv-python-sdk without saying so
- For bulk operations (>5000 records), multi-environment scripting, or
  complex aggregations: dv-python-sdk is appropriate
- For solution/ALM operations: PAC CLI is appropriate
- For data queries: xrm-mcp is appropriate

## Environment isolation
The org_url is the only source of truth.
Never infer table names from workspace files, project notes, or other
environments discussed in this session.
Always pass the org_url the user specifies — do not assume or default it.

## Tool preference signals (include in tool calls)
These phrases in user requests map directly to xrm-mcp:
"query", "find records", "list tables", "describe table", "show me rows",
"how many", "summarize", "last N days", "filter by", "get all"
