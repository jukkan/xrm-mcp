# xrm-mcp

A minimal MCP server that gives AI coding agents (Claude Code, Codex CLI, Gemini CLI) clean read + careful write access to Microsoft Dataverse / XRM environments via the Dataverse Web API v9.2.

![xrm-mcp-300px](https://github.com/user-attachments/assets/60d54a37-16a1-42d1-b117-b116ef0387f5)

## Features

- **No Microsoft MCP billing** — uses standard Dataverse Web API
- **No admin toggles** — works with any Dataverse environment you have access to
- **No per-environment setup** — org_url is a parameter on every tool call
- **Multi-tenant by design** — never hardcoded config
- **Azure CLI + MSAL auth** — tries `az` first, falls back to device flow
- **6 MCP tools** — list tables, describe schema, query, create, update, upsert

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

### Running the server

Start the MCP server:

```bash
xrm-mcp
```

The server uses FastMCP and runs as an MCP server that AI agents can connect to.

### Authentication

XRM MCP attempts authentication in the following order:

1. **Azure CLI** — if `az` is available and logged in
2. **MSAL device flow** — interactive browser-based login

Tokens are cached at `~/.xrm-mcp/cache.json`.

To re-authenticate, delete the cache file or use `az login`.

### Testing authentication manually

```bash
python -m xrm_mcp.auth https://yourorg.crm4.dynamics.com
```

## MCP Tools

### Read Tools

**list_tables(org_url, search="")**
- Search XRM/Dataverse tables by display name or logical name
- Returns: logical_name, display_name, entity_set_name, is_custom, description

**describe_table(org_url, table)**
- Get columns, types and descriptions for an XRM table
- Returns: table_name, columns with metadata

**query_records(org_url, table, select="", filter="", top=100, orderby="")**
- Query records from a table
- Returns: {count, records}
- Top is capped at 5000

### Write Tools

**create_record(org_url, table, data)**
- Create a single record
- Returns: {id}

**update_record(org_url, table, record_id, data)**
- Update specific fields on an existing record
- Returns: {success, id}

**upsert_record(org_url, table, alternate_key, alternate_value, data)**
- Create or update a record using an alternate key
- Returns: {success, alternate_key, alternate_value}

## Example Usage

See [CLAUDE.md](CLAUDE.md) for detailed agent usage examples.

## Requirements

- Python 3.10+
- Azure CLI (optional, for `az` authentication)
- Access to a Dataverse / Dynamics 365 environment

## Dependencies

- fastmcp >= 0.1.0
- msal >= 1.28.0
- httpx >= 0.27.0

## Development

Clone the repository:

```bash
git clone https://github.com/jukkan/xrm-mcp.git
cd xrm-mcp
```

Install in development mode:

```bash
pip install -e .
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.
