# XRM MCP — Agent Guide

XRM MCP gives you direct read and write access to any Dataverse / XRM environment via its Web API. No Microsoft MCP billing. No admin setup per environment. Pass the org URL with every call.

## Decision tree

- First time connecting to an environment → call ping first to verify setup
- User names a table in business language ("hour entries", "work orders") → call list_tables with search term first
- User names a table you recognise → call query_records directly
- You need column names for filter or select → call describe_table first
- Writing data → use create_record, update_record, or upsert_record
- Never assume a table's logical name. Never default the org_url. Always ask the user if org_url not provided.

### Environment isolation rule
The target org_url is the only source of truth for schema.
NEVER infer table names, column names, or schema from:
- Local project files or .md notes
- Other environments previously discussed
- Client project descriptions in the workspace
- Solution files or YAML in the repo

If a user says "hour entry" and you don't know the logical name in THIS
org, call find_table(org_url, "hour entry") — do not guess.

### Discovery failure rule
If find_table or list_tables returns no results or an error, stop and
tell the user: "I can't identify that table in {org_url} with the
available tools. Can you provide the logical table name?"
Do not substitute workspace context for missing environment data.

### Revised decision tree

User gives a friendly table name ("hour entry", "projects", "deals"):
  → find_table(org_url, "hour entry")

User gives a logical name you recognise from this session's list_tables:
  → describe_table(org_url, logical_name)

You need column names before querying:
  → describe_table(org_url, logical_name)

Column names unknown and query returns 400:
  → describe_table first, then retry query with exact column names

**list_tables usage patterns:**
- First call (focused custom table list): list_tables(org_url)
- User's own tables: list_tables(org_url, prefix="na_")
- Everything: list_tables(org_url, exclude_ms_prefixes=False)
- Search: list_tables(org_url, search="hour")

## Example: "get hour entries from last 30 days from https://niiranen-prod.crm4.dynamics.com"

**Step 0 (first time):** ping(org_url="https://niiranen-prod.crm4.dynamics.com")
→ returns {status: "ok", org_url: "...", user_id: "...", business_unit_id: "...", org_id: "..."}

**Step 1:** list_tables(org_url="https://niiranen-prod.crm4.dynamics.com", search="hour")
→ returns [{logical_name: "cr123_hourentry", ...}]

**Step 2:** describe_table(org_url="https://niiranen-prod.crm4.dynamics.com", table="cr123_hourentry")
→ returns columns including "cr123_date", "cr123_hours", etc.

**Step 3:** query_records(
  org_url="https://niiranen-prod.crm4.dynamics.com",
  table="cr123_hourentry",
  select="cr123_date,cr123_hours,cr123_description",
  filter="cr123_date ge 2024-03-01",
  top=1000
)
→ returns {count: 42, records: [...]}

## Tools summary

### Read tools

**ping(org_url)**
Verify connectivity and authentication to a Dataverse environment. Returns {status, org_url, user_id, business_unit_id, org_id}. Call this first when connecting to a new environment.

**find_table(org_url, name)**
Search for a table by display name or partial logical name. Use this when the user gives a friendly name like 'hour entry' or 'hours' and you don't know the exact logical name. Returns all candidate matches from this specific environment — do not use workspace files or project notes to infer table names.

**list_tables(org_url, search="", custom_only=True, prefix="", exclude_ms_prefixes=True)**
Search tables by display name or logical name. Use this when the user refers to a table by a business name. By default, only custom entities are returned (custom_only=True) and Microsoft-prefixed solution tables are excluded (exclude_ms_prefixes=True). Use prefix to filter by logical name prefix.

**describe_table(org_url, table)**
Get column metadata for a table. Use this before querying to find column names.

**query_records(org_url, table, select="", filter="", top=100, orderby="")**
Query records from a table. Returns {count, records}.

### Write tools

**create_record(org_url, table, data)**
Create a single record. Returns {id}.

**update_record(org_url, table, record_id, data)**
Update specific fields on an existing record.

**upsert_record(org_url, table, alternate_key, alternate_value, data)**
Create or update a record using an alternate key (for sync/import scenarios).

## Tips

- Always use logical names (lowercase, underscores) for tables and columns
- OData filter syntax: `cr123_status eq 1 and cr123_date ge 2024-01-01`
- Top is capped at 5000 records per query
- For lookups, use the navigation property name (usually ends with `_id`)
- Date filters use ISO format: `2024-03-01T00:00:00Z`

## Authentication

XRM MCP tries Azure CLI first (`az account get-access-token`), then falls back to interactive device flow via MSAL. Tokens are cached at `~/.xrm-mcp/cache.json`.

If you need to re-authenticate, delete the cache file or use `az login` to refresh Azure CLI credentials.
