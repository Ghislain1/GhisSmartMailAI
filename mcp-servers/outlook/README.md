# Outlook MCP Server

MCP server that reads and writes Outlook emails via Microsoft Graph (app-only / client credentials).

## Tools

- `list_messages(folder="inbox", top=10, unread_only=False)` - list messages from a folder
- `get_message(message_id, include_body=True)` - fetch a message (optionally with body)
- `search_messages(query, top=10)` - search messages
- `send_email(to, subject, body, cc?, bcc?, content_type="Text", save_to_sent_items=True)` - send mail
- `create_draft(to, subject, body, cc?, bcc?, content_type="Text")` - create draft
- `reply_to_message(message_id, comment, reply_all=False)` - reply / reply-all
- `forward_message(message_id, to, comment="")` - forward
- `update_message(message_id, is_read=bool)` - mark read/unread
- `move_message(message_id, destination_folder)` - move to folder (e.g. `archive`, `deleteditems`)

## Prerequisites

- Azure AD app registration with **Application** permissions for Microsoft Graph:
  - `Mail.ReadWrite`, `Mail.Send` (grant admin consent)
- Client secret for the app
- A target mailbox (`OUTLOOK_USER_ID` = user id/UPN, or `me` only for delegated flows)

## Configuration

Create `.env` (or export variables):

```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
OUTLOOK_USER_ID=user@contoso.com
```

## Run

```bash
cd mcp-servers/outlook
uv sync
uv run outlook-mcp-server
```

The server runs over stdio (MCP). Example client config:

```json
{
  "mcpServers": {
    "outlook": {
      "command": "uv",
      "args": ["--directory", "mcp-servers/outlook", "run", "outlook-mcp-server"],
      "env": {
        "AZURE_TENANT_ID": "...",
        "AZURE_CLIENT_ID": "...",
        "AZURE_CLIENT_SECRET": "...",
        "OUTLOOK_USER_ID": "user@contoso.com"
      }
    }
  }
}
```
