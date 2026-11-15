from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .graph import GraphClient

mcp = FastMCP("outlook-mcp-server")

_client: GraphClient | None = None


def _get_client() -> GraphClient:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.is_configured:
            raise RuntimeError(
                "Outlook MCP server is not configured. Set AZURE_TENANT_ID, "
                "AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET."
            )
        _client = GraphClient(settings)
    return _client


def _recipients(addresses: list[str] | str | None) -> list[dict[str, Any]]:
    if not addresses:
        return []
    if isinstance(addresses, str):
        addresses = [a.strip() for a in addresses.split(",") if a.strip()]
    return [{"emailAddress": {"address": a}} for a in addresses]


def _simplify_message(msg: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": msg.get("id"),
        "subject": msg.get("subject"),
        "from": (msg.get("from") or {}).get("emailAddress"),
        "toRecipients": [r.get("emailAddress") for r in msg.get("toRecipients", [])],
        "receivedDateTime": msg.get("receivedDateTime"),
        "sentDateTime": msg.get("sentDateTime"),
        "isRead": msg.get("isRead"),
        "isDraft": msg.get("isDraft"),
        "bodyPreview": msg.get("bodyPreview"),
        "webLink": msg.get("webLink"),
        "importance": msg.get("importance"),
        "hasAttachments": msg.get("hasAttachments"),
    }


@mcp.tool()
def list_messages(
    folder: str = "inbox",
    top: int = 10,
    unread_only: bool = False,
) -> str:
    """List email messages from a mail folder (default: inbox)."""
    params: dict[str, Any] = {
        "$top": max(1, min(top, 50)),
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,toRecipients,receivedDateTime,sentDateTime,isRead,isDraft,bodyPreview,webLink,importance,hasAttachments",
    }
    if unread_only:
        params["$filter"] = "isRead eq false"
    data = _get_client().get(f"mailFolders/{folder}/messages", params=params)
    messages = [_simplify_message(m) for m in data.get("value", [])]
    return json.dumps({"count": len(messages), "messages": messages}, ensure_ascii=False)


@mcp.tool()
def get_message(message_id: str, include_body: bool = True) -> str:
    """Get a single email message by id, including full body by default."""
    select = "id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,sentDateTime,isRead,isDraft,bodyPreview,body,webLink,importance,hasAttachments"
    if not include_body:
        select = select.replace(",body", "")
    data = _get_client().get(f"messages/{message_id}", params={"$select": select})
    result = _simplify_message(data)
    if include_body and "body" in data:
        result["body"] = data["body"]
    result["ccRecipients"] = [r.get("emailAddress") for r in data.get("ccRecipients", [])]
    result["bccRecipients"] = [r.get("emailAddress") for r in data.get("bccRecipients", [])]
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def search_messages(query: str, top: int = 10) -> str:
    """Search email messages by query string."""
    params: dict[str, Any] = {
        "$search": f'"{query}"',
        "$top": max(1, min(top, 50)),
        "$select": "id,subject,from,toRecipients,receivedDateTime,isRead,isDraft,bodyPreview,webLink,importance,hasAttachments",
    }
    data = _get_client().get("messages", params=params)
    messages = [_simplify_message(m) for m in data.get("value", [])]
    return json.dumps({"count": len(messages), "messages": messages}, ensure_ascii=False)


@mcp.tool()
def send_email(
    to: str | list[str],
    subject: str,
    body: str,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
    content_type: str = "Text",
    save_to_sent_items: bool = True,
) -> str:
    """Send an email. `to`/`cc`/`bcc` can be an address or list/comma-separated string."""
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": content_type, "content": body},
            "toRecipients": _recipients(to),
            "ccRecipients": _recipients(cc),
            "bccRecipients": _recipients(bcc),
        },
        "saveToSentItems": save_to_sent_items,
    }
    _get_client().post("sendMail", json=payload)
    return json.dumps({"status": "sent", "subject": subject, "to": _recipients(to)}, ensure_ascii=False)


@mcp.tool()
def create_draft(
    to: str | list[str],
    subject: str,
    body: str,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
    content_type: str = "Text",
) -> str:
    """Create a draft email message."""
    payload = {
        "subject": subject,
        "body": {"contentType": content_type, "content": body},
        "toRecipients": _recipients(to),
        "ccRecipients": _recipients(cc),
        "bccRecipients": _recipients(bcc),
    }
    data = _get_client().post("messages", json=payload)
    return json.dumps({"status": "draft_created", "id": data.get("id"), "subject": subject}, ensure_ascii=False)


@mcp.tool()
def reply_to_message(message_id: str, comment: str, reply_all: bool = False) -> str:
    """Reply to an email message. Set reply_all=True to reply to all recipients."""
    action = "replyAll" if reply_all else "reply"
    _get_client().post(f"messages/{message_id}/{action}", json={"comment": comment})
    return json.dumps({"status": "replied", "message_id": message_id, "reply_all": reply_all}, ensure_ascii=False)


@mcp.tool()
def forward_message(message_id: str, to: str | list[str], comment: str = "") -> str:
    """Forward an email message to recipients."""
    _get_client().post(
        f"messages/{message_id}/forward",
        json={"comment": comment, "toRecipients": _recipients(to)},
    )
    return json.dumps({"status": "forwarded", "message_id": message_id, "to": _recipients(to)}, ensure_ascii=False)


@mcp.tool()
def update_message(message_id: str, is_read: bool | None = None) -> str:
    """Update message properties (currently supports marking read/unread)."""
    payload: dict[str, Any] = {}
    if is_read is not None:
        payload["isRead"] = is_read
    if not payload:
        return json.dumps({"status": "no_changes", "message_id": message_id})
    _get_client().patch(f"messages/{message_id}", json=payload)
    return json.dumps({"status": "updated", "message_id": message_id, "updated": payload}, ensure_ascii=False)


@mcp.tool()
def move_message(message_id: str, destination_folder: str) -> str:
    """Move a message to another folder (e.g. 'archive', 'deleteditems', or a folder id)."""
    data = _get_client().post(f"messages/{message_id}/move", json={"destinationId": destination_folder})
    return json.dumps({"status": "moved", "message_id": data.get("id", message_id), "destination": destination_folder}, ensure_ascii=False)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
