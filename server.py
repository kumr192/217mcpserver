import os
import random
import sys
from datetime import datetime, timezone

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
SERVER_NAME = "QuoteBox"
SERVER_VERSION = "1.0.0"

mcp = FastMCP(SERVER_NAME)

# --- Data ---

QUOTES = {
    "motivation": [
        "The only way to do great work is to love what you do. — Steve Jobs",
        "It does not matter how slowly you go as long as you do not stop. — Confucius",
        "Everything you've ever wanted is on the other side of fear. — George Addair",
        "Believe you can and you're halfway there. — Theodore Roosevelt",
    ],
    "wisdom": [
        "The unexamined life is not worth living. — Socrates",
        "In the middle of difficulty lies opportunity. — Albert Einstein",
        "The secret of getting ahead is getting started. — Mark Twain",
        "An investment in knowledge pays the best interest. — Benjamin Franklin",
    ],
    "humor": [
        "I am so clever that sometimes I don't understand a single word of what I am saying. — Oscar Wilde",
        "Always borrow money from a pessimist. They never expect it back. — Unknown",
        "I didn't fail the test. I just found 100 ways to do it wrong. — Benjamin Franklin",
        "Behind every great man is a woman rolling her eyes. — Jim Carrey",
    ],
}

ALL_QUOTES = [q for qs in QUOTES.values() for q in qs]

# --- Manual Tool Definitions (For the Smart Handler) ---
# We define these explicitly so we can send them even if Drsti asks the wrong endpoint.

TOOL_DEFINITIONS = [
    {
        "name": "get_quote",
        "description": "Get a random quote.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "One of 'motivation', 'wisdom', 'humor', or 'any'."
                }
            }
        }
    },
    {
        "name": "format_message",
        "description": "Format a message in a fun way.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The text to format."},
                "style": {"type": "string", "description": "One of 'box', 'reverse', 'shout', 'banner'."}
            },
            "required": ["message"]
        }
    },
    {
        "name": "server_info",
        "description": "Get metadata about this MCP server.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

# --- MCP Tool Logic ---

@mcp.tool()
def get_quote(category: str = "any") -> str:
    """Get a random quote.
    Args:
        category: One of 'motivation', 'wisdom', 'humor', or 'any' for a random pick.
    """
    cat = category.lower().strip()
    if cat == "any":
        return random.choice(ALL_QUOTES)
    if cat not in QUOTES:
        return f"Unknown category '{cat}'. Choose from: motivation, wisdom, humor, any."
    return random.choice(QUOTES[cat])

def _style_box(msg: str) -> str:
    lines = msg.split("\n")
    width = max(len(line) for line in lines)
    border = "*" * (width + 4)
    body = "\n".join(f"* {line:<{width}} *" for line in lines)
    return f"{border}\n{body}\n{border}"

def _style_reverse(msg: str) -> str:
    return msg[::-1]

def _style_shout(msg: str) -> str:
    return " ! ".join(msg.upper().split()) + " !!!"

def _style_banner(msg: str) -> str:
    return "  ".join(c.upper() * 3 for c in msg if c.strip())

STYLES = {
    "box": _style_box,
    "reverse": _style_reverse,
    "shout": _style_shout,
    "banner": _style_banner,
}

@mcp.tool()
def format_message(message: str, style: str = "box") -> str:
    """Format a message in a fun way.
    Args:
        message: The text to format.
        style: One of 'box' (ASCII border), 'reverse' (backwards), 'shout' (LOUD), 'banner' (tripled letters).
    """
    s = style.lower().strip()
    if s not in STYLES:
        return f"Unknown style '{s}'. Choose from: box, reverse, shout, banner."
    return STYLES[s](message)

@mcp.tool()
def server_info() -> str:
    """Get metadata about this MCP server."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    tools = ["get_quote", "format_message", "server_info"]
    return "\n".join([
        f"Server : {SERVER_NAME} v{SERVER_VERSION}",
        f"Python : {sys.version.split()[0]}",
        f"Tools  : {', '.join(tools)}",
        f"Time   : {now}",
    ])

# --- The Smart Handler (The Fix) ---

async def handle_sse_post_smart(request):
    """
    Handles Drsti.ai's requests.
    1. If it's a Health Check -> Returns {status: online}
    2. If it's a Tool List Request -> Returns the Tool List JSON
    """
    try:
        body = await request.json()
    except:
        body = {}

    # Check if Drsti is asking for the tool list (method: tools/list)
    if isinstance(body, dict) and body.get("method") == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id", 1),
            "result": {
                "tools": TOOL_DEFINITIONS
            }
        })

    # Otherwise, assume it's a health check
    return JSONResponse({"status": "online", "protocol": "sse"})

# --- Server Setup ---

mcp_app = mcp.sse_app()

routes = [
    # Intercept POST /sse with our smart handler
    Route("/sse", handle_sse_post_smart, methods=["POST"]),
    # Handle normal SSE traffic
    Mount("/", app=mcp_app)
]

app = Starlette(routes=routes)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
