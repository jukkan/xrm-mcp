# xrm-mcp

A minimal MCP server that gives AI coding agents (Claude Code, GitHub Copilot, Codex CLI, Cursor, Gemini CLI) clean read + careful write access to Microsoft Dataverse / XRM environments via the Dataverse Web API v9.2.

![xrm-mcp-300px](https://github.com/user-attachments/assets/60d54a37-16a1-42d1-b117-b116ef0387f5)

> **Why this exists**: Microsoft ships its own Dataverse MCP server, but it requires Power Platform admin setup, Managed Environments, and Copilot Credits per call. `xrm-mcp` is a drop-in alternative that works with any Dataverse environment using your existing Azure CLI or Microsoft account. [Read more →](WHY.md)

## Features

- **No Microsoft MCP billing** — calls the Dataverse Web API directly, no Copilot Credits consumed
- **No admin toggles** — works with any Dataverse environment you can log into
- **No Managed Environment required** — standard environments work fine
- **No per-environment setup** — org_url is a parameter on every tool call
- **Multi-tenant by design** — connect to multiple orgs in the same session, with per-environment identity caching so switching between tenants doesn't require re-authenticating each time
- **Azure CLI + MSAL auth** — tries `az` first, falls back to interactive device flow
- **8 MCP tools** — ping, find/list tables, describe schema, query, create, update, upsert

## Installation

Install via pipx (recommended):

```bash
pipx install git+https://github.com/jukkan/xrm-mcp.git
```

Or via pip:

```bash
pip install git+https://github.com/jukkan/xrm-mcp.git
```

## Usage

### Configuring your AI agent

Add `xrm-mcp` to your agent's MCP configuration.

**Claude Desktop / Claude Code** (`~/.claude/claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "xrm-mcp": {
      "command": "xrm-mcp"
    }
  }
}
```

**GitHub Copilot (VS Code)** — add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "xrm-mcp": {
      "type": "stdio",
      "command": "xrm-mcp"
    }
  }
}
```

Once configured, pass your environment URL with every request and the agent takes it from there:

> *"Show me all project records from https://myorg.crm4.dynamics.com created in the last 30 days"*

### Running the server manually

```bash
xrm-mcp
```

The server uses FastMCP and communicates over stdin/stdout (stdio transport).

### Authentication

XRM MCP attempts authentication in the following order:

1. **Azure CLI** — if `az` is available and logged in
2. **MSAL device flow** — interactive browser-based login

Tokens are cached at `~/.xrm-mcp/cache.json`.

If you work across multiple tenants (e.g. your own production environment, demo
environments, and customer tenants), XRM MCP remembers which identity last
worked for each `org_url` in `~/.xrm-mcp/identity_cache.json` and prefers it on
the next call — so switching tenants doesn't depend on which `az` account
happens to be active. If a call gets a `401`/`403`, that org's cached identity
is cleared automatically and the error message tells you to just retry, which
re-discovers a working identity.

To re-authenticate, delete `~/.xrm-mcp/cache.json` or use `az login`. To reset
which identity is used for a specific org, delete its entry from
`~/.xrm-mcp/identity_cache.json`.

### Testing authentication manually

```bash
python -m xrm_mcp.auth https://yourorg.crm4.dynamics.com
```

## MCP Tools

### Read Tools

**ping(org_url)**
- Verify connectivity and authentication to a Dataverse environment
- Returns: status, org_url, user_id, business_unit_id, org_id, auth_method, tenant_id
- Call this first when connecting to a new environment; `auth_method`/`tenant_id` let you confirm which identity answered the call

**find_table(org_url, name)**
- Search for a table by display name or partial logical name
- Use when the user says "hour entries" and you need the exact logical name
- Returns all matching tables sorted by exact display name match first

**list_tables(org_url, search="", custom_only=True, prefix="", exclude_ms_prefixes=True)**
- List Dataverse tables, defaulting to custom entities only
- `custom_only=True` — only return custom entities (default)
- `prefix="na_"` — filter to a specific publisher prefix
- `exclude_ms_prefixes=False` — include Microsoft solution tables (msdyn\_, adx\_, etc.)
- Returns: logical_name, display_name, entity_set_name, is_custom, description

**describe_table(org_url, table)**
- Get columns, types and descriptions for a Dataverse table
- Call this before querying when you need exact column names for $select or $filter
- Returns: table_name, columns with metadata

**query_records(org_url, table, select="", filter="", top=100, orderby="")**
- Query records from a table using OData filter syntax
- Returns: {count, records}
- Top is capped at 5000
- `select` is validated against real column names before querying; an invalid column raises a clear error naming it, instead of silently returning every column

### Write Tools

**create_record(org_url, table, data)**
- Create a single record
- Returns: {id}

**update_record(org_url, table, record_id, data)**
- Update specific fields on an existing record
- Returns: {success, id}

**upsert_record(org_url, table, alternate_key, alternate_value, data)**
- Create or update a record using an alternate key (for sync/import scenarios)
- Returns: {success, alternate_key, alternate_value}

## Example Usage

See [CLAUDE.md](CLAUDE.md) for detailed agent usage examples and [WHY.md](WHY.md) for how this compares to Microsoft's own Dataverse MCP server.

## Requirements

- Python 3.10+
- Azure CLI (optional, for `az` authentication)
- Access to a Dataverse / Dynamics 365 environment

## Dependencies

- fastmcp >= 3.0, < 4
- msal >= 1.28.0, < 2
- httpx >= 0.27.0, < 1

Version 0.2.0 moved from FastMCP 2.x to FastMCP 3.x. Existing installs need to
be reinstalled (for example `pipx reinstall xrm-mcp` or
`uv tool install --force ...`) so the new FastMCP version is resolved.

## Development

Clone the repository:

```bash
git clone https://github.com/jukkan/xrm-mcp.git
cd xrm-mcp
```

Install in development mode:

```bash
pip install -e ".[dev]"
```

Run the tests (no Dataverse environment or credentials required):

```bash
pytest
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.
