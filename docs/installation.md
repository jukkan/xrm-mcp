# Install xrm-mcp on your computer

Requires Python 3.10+, Git (for the GitHub install URLs), and access to a Dataverse environment. Azure CLI is optional. Install on each computer where your MCP client runs. The examples below use `vX.Y.Z` as a placeholder: replace it with an **existing** tag from [the repository's tags](https://github.com/jukkan/xrm-mcp/tags). If no tag has been published yet, omit `@vX.Y.Z` to install the current repository version; pin to a tag when one is available.

## Install

**Recommended: isolated tool environment.** Install [uv](https://docs.astral.sh/uv/getting-started/installation/) or [pipx](https://pipx.pypa.io/stable/installation/) first, then choose one:

```sh
uv tool install "git+https://github.com/jukkan/xrm-mcp.git@vX.Y.Z"
# or
pipx install "git+https://github.com/jukkan/xrm-mcp.git@vX.Y.Z"
```

Alternatively, use a dedicated virtual environment (do not install into your system Python):

| macOS/Linux | Windows PowerShell |
| --- | --- |
| `python3 -m venv .venv` | `py -3 -m venv .venv` |
| `. .venv/bin/activate` | `.\.venv\Scripts\Activate.ps1` |

With the environment active:

```sh
python -m pip install "git+https://github.com/jukkan/xrm-mcp.git@vX.Y.Z"
```

For a **plain pip** installation without a virtual environment, the same `python -m pip install ...` command works, but an isolated environment avoids conflicts with other Python packages. A virtual environment's `xrm-mcp` executable lives in `.venv/bin/` (macOS/Linux) or `.venv\Scripts\` (Windows).

## Connect a stdio MCP client

For an installed tool, use `xrm-mcp` with no arguments. **Claude Desktop** uses `claude_desktop_config.json` (`~/Library/Application Support/Claude/` on macOS or `%APPDATA%\Claude\` on Windows). **Claude Code** can use the same `mcpServers` block in a project-root `.mcp.json`:

```json
{
  "mcpServers": {
    "xrm-mcp": {
      "command": "xrm-mcp",
      "args": []
    }
  }
}
```

**GitHub Copilot in VS Code** uses `.vscode/mcp.json` in the workspace:

```json
{
  "servers": {
    "xrm-mcp": {
      "type": "stdio",
      "command": "xrm-mcp",
      "args": []
    }
  }
}
```

Alternatively, to **run directly from a pinned tag without installing xrm-mcp**, install uv and replace the `command` and `args` in *either* client config with:

```json
{
  "command": "uvx",
  "args": ["--from", "git+https://github.com/jukkan/xrm-mcp.git@vX.Y.Z", "xrm-mcp"]
}
```

`uvx` manages its own cached environment; the first start may take longer. Replace `vX.Y.Z` with an existing tag. If the client cannot find `xrm-mcp` or `uvx` (especially when launched from a desktop icon), use its absolute executable path as `command`: find it with `command -v xrm-mcp` / `command -v uvx` on macOS/Linux or `where.exe xrm-mcp` / `where.exe uvx` on Windows. For virtual environments, point `command` directly at that environment's executable rather than relying on shell activation. In JSON, escape Windows path separators (`\\`).

## Upgrade, rollback, and authenticate

To upgrade **or roll back**, substitute the desired published tag in your original install command. For existing tool installs, use `uv tool install --force "git+https://github.com/jukkan/xrm-mcp.git@vX.Y.Z"` or `pipx install --force "git+https://github.com/jukkan/xrm-mcp.git@vX.Y.Z"`; in an activated virtual environment, use `python -m pip install --force-reinstall "git+https://github.com/jukkan/xrm-mcp.git@vX.Y.Z"`. For `uvx`, change the tag in the client config. Restart Claude Desktop/Claude Code or VS Code after changing an installation or config so it launches the new version.

On first use, call `ping` with your Dataverse `org_url` (for example, `https://yourorg.crm4.dynamics.com`); check `auth_method` and `tenant_id` in the result. If you use Azure CLI, install it and run `az login` (or `az login --tenant <tenant-id>` for a specific tenant). Otherwise xrm-mcp prompts for MSAL device-code sign-in when it needs a token. It caches MSAL tokens in `~/.xrm-mcp/cache.json` and the last working identity per org in `~/.xrm-mcp/identity_cache.json` (under `%USERPROFILE%\.xrm-mcp\` on Windows).

## Troubleshooting

- **Command not found / server won't start:** Check that Git, Python 3.10+, and your chosen installer are available. Verify the executable path in the client config; for `uvx`, confirm that the tag exists and that the client can reach GitHub on first run. Check the client's MCP/server logs for startup errors; device-code prompts appear on stderr.
- **Authentication fails:** Confirm the org URL, tenant, account access, and network connection. After a `401`/`403`, retry: xrm-mcp clears that org's cached identity. Run `az login` for the right account/tenant if needed. If MSAL sign-in is stuck, delete `cache.json` to re-authenticate; to forget a specific org's preferred identity, remove its entry from `identity_cache.json` (or delete the file to reset all orgs). Restart the client and retry `ping`.
