# Why xrm-mcp?

A plain-language explanation of how this tool works, who it is for, and how it differs from Microsoft's own Dataverse MCP server.

---

## What is an MCP server?

MCP stands for **Model Context Protocol**. It is an open standard (introduced by Anthropic in late 2024) that lets AI assistants — like Claude, GitHub Copilot, or Cursor — connect to external systems in a structured way.

Without MCP, an AI assistant can only work with what you paste into the chat. With MCP, the assistant can directly call tools: look up records, read a schema, create or update data — all without you having to copy-paste anything.

Think of it like a plug socket: any AI agent that supports MCP can plug into any MCP server, including this one, and immediately get the tools it needs to work with your data.

---

## How xrm-mcp works in practice

When you connect an AI agent to `xrm-mcp` and ask it a question like:

> *"Show me all open projects created this month from https://myorg.crm4.dynamics.com"*

…the agent does not write raw code or guess at field names. Instead, it works through a short discovery sequence using the tools this server provides:

1. **ping** — confirms it can reach your environment and that your credentials work
2. **find_table** — searches for a table matching "projects" and finds the exact logical name (e.g., `na_project`)
3. **describe_table** — inspects that table's columns to find out which field holds the creation date and status
4. **query_records** — fetches the matching records using those exact field names

The agent adapts to *your* schema. It never hardcodes field names or guesses at table structures. Every query is grounded in what actually exists in your specific environment.

---

## Why this is different from raw Web API calls

If you tried to do the same thing by hand with the Dataverse Web API, you would need to:

- Know the exact OData endpoint URL format
- Know the entity set name (e.g., `na_projects` not `na_project`)
- Know which fields exist and their exact logical names
- Handle authentication tokens yourself
- Parse the response format (which includes annotation noise like `@odata.etag`)
- Manage pagination if the result is large

An AI agent hitting the Web API directly without MCP would have to guess all of this, or you would have to tell it manually in every prompt. With `xrm-mcp`, the agent discovers all of this dynamically. It asks the environment itself what exists — then uses exactly that. No guessing, no copy-pasting field names into prompts.

`xrm-mcp` also silently cleans up API response noise (OData annotations, raw option set codes, lookup GUIDs) and returns human-readable values — so the agent sees `"Status: Active"` rather than `"statuscode: 1"`.

---

## Microsoft's official Dataverse MCP server

Microsoft released its own Dataverse MCP server as part of Power Platform. It exposes the same idea — Dataverse data as MCP tools — but it is built as a hosted service within the Power Platform infrastructure.

**What it offers:**
- Tight integration with Copilot Studio (Microsoft's low-code agent builder)
- Access to advanced capabilities like Dataverse search and relationship traversal
- Part of the official Microsoft 365 / Power Platform ecosystem

**What it requires:**

| Requirement | Detail |
|---|---|
| Power Platform admin | An admin must enable the MCP server in the Power Platform Admin Center |
| Managed Environment | Only available for Managed Environments (a premium tier) |
| Copilot Credits | Each tool call outside Copilot Studio consumes Copilot Credits |
| Dynamics 365 Premium license | Required to access D365 data (Sales, Finance, etc.) through the MCP server |
| Power Platform CLI + .NET 8 | Required to connect local agent tools like Claude or VS Code |
| Client allowlisting | Copilot Studio is the only allowed client by default; others must be explicitly enabled per environment |

In short: the Microsoft MCP server is a managed cloud service governed by the Power Platform, and using it from any AI agent *other than* Copilot Studio requires several administrative steps, the right licensing tier, and consumes usage credits on every call.

---

## Why xrm-mcp is useful

`xrm-mcp` is a lightweight open-source alternative that calls the standard Dataverse Web API directly. There is no middleware, no cloud billing layer, and no admin prerequisite.

| | xrm-mcp | Microsoft Dataverse MCP |
|---|---|---|
| Admin setup required | ✗ None | ✓ Power Platform Admin Center |
| Managed Environment required | ✗ No | ✓ Yes |
| Copilot Credits consumed | ✗ No | ✓ Yes (outside Copilot Studio) |
| D365 Premium license needed | ✗ No | ✓ For D365 data |
| Works with any Dataverse env | ✓ Yes | ✗ Managed Environments only |
| Works with Claude, Copilot, Cursor | ✓ Yes | ✓ With admin enablement |
| Authentication | Azure CLI or MSAL device flow | Entra ID (OAuth) |
| Multi-org in one session | ✓ Yes (org_url per call) | ✗ One env per connection |

If you already have access to a Dataverse environment and a Microsoft account, `xrm-mcp` works immediately — with no IT ticket, no admin approval, and no monthly billing counter.

---

## A note on Dataverse Skills

Microsoft also maintains an open-source project called [Dataverse Skills](https://github.com/microsoft/Dataverse-skills) — a set of YAML/Markdown files that describe business processes agents can follow. These skills are designed to work alongside the Microsoft Dataverse MCP server.

Some of those skills are built specifically to call the Microsoft Dataverse MCP API endpoint (`/api/mcp`) rather than the Web API. Those skills **will not work** with `xrm-mcp` because `xrm-mcp` does not implement the same server-side endpoint format.

However, because `xrm-mcp` exposes its own set of well-documented tools, any agent (Claude Code, GitHub Copilot, Cursor, Gemini CLI) can use the [CLAUDE.md](CLAUDE.md) and [SKILL.md](SKILL.md) files as its instruction set for working with Dataverse — effectively playing the same role as those skills, but routing through the Web API instead of the Microsoft-managed MCP endpoint.

---

## Who is xrm-mcp for?

- **Developers** who want their AI coding assistant to query or update Dataverse data during development, without waiting for IT to enable a managed service
- **Power Platform consultants** working across multiple client environments who want a single tool that works everywhere with their own credentials
- **Makers and analysts** who want to use Claude, GitHub Copilot, or another AI tool to explore data and generate reports from Dataverse — without spinning up a premium infrastructure
- **Anyone** who has a Dynamics 365 or Power Apps environment and wants their AI assistant to be able to look things up in it
