import os
import random
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Initialize
SERVER_NAME = "RajiniKamalBot"
mcp = FastMCP(SERVER_NAME)

# --- The Content ---

RAJINI_JOKES = [
    "Rajinikanth can delete the Recycle Bin.",
    "Rajinikanth knows the last digit of Pi.",
    "When Rajinikanth does a pushup, he isn't lifting himself up, he's pushing the Earth down.",
    "Rajinikanth once kicked a horse in the chin. Its descendants are now known as Giraffes.",
    "Rajinikanth can strangle you with a cordless phone.",
    "Google searches for Rajinikanth because it knows he can find anything.",
]

KAMAL_QUOTES = [
    "I am a hero who wants to be a villain. — Kamal Haasan",
    "Art is a lie that makes us realize the truth. — Kamal Haasan",
    "I don't believe in boundaries. I am an artist, the world is my stage. — Kamal Haasan",
    "Failure is the only way to learn. Success is just the ego boost. — Kamal Haasan",
    "Mediocrity is a sin in my book. — Kamal Haasan",
    "Sympathy is a reaction. Empathy is an action. — Kamal Haasan",
]

# --- The Tool Definition ---

TOOL_DEFINITIONS = [
    {
        "name": "get_entertainment",
        "description": "Get a Rajinikanth joke or a Kamal Haasan quote.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Either 'rajini' (for jokes) or 'kamal' (for wisdom)."
                }
            },
            "required": ["category"]
        }
    }
]

# --- The Logic ---

@mcp.tool()
def get_entertainment(category: str) -> str:
    """Get a Rajini joke or Kamal quote."""
    cat = category.lower().strip()
    
    if "rajini" in cat:
        return f"😎 THALAIVAR SAYS: {random.choice(RAJINI_JOKES)}"
    elif "kamal" in cat:
        return f"🎭 ULAGANAYAGAN SAYS: {random.choice(KAMAL_QUOTES)}"
    else:
        return "Please choose either 'rajini' or 'kamal'."

# --- The Connection Fix (Crucial for Drsti) ---

async def handle_drsti_connection(request):
    """
    Handles Drsti.ai's connection checks.
    """
    try:
        body = await request.json()
    except:
        body = {}

    # If Drsti asks for tools, give them the list
    if isinstance(body, dict) and body.get("method") == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id", 1),
            "result": { "tools": TOOL_DEFINITIONS }
        })

    # Otherwise, just say we are online
    return JSONResponse({"status": "online", "protocol": "sse"})

# --- Run Server ---

mcp_app = mcp.sse_app()

routes = [
    Route("/sse", handle_drsti_connection, methods=["POST"]),
    Mount("/", app=mcp_app)
]

app = Starlette(routes=routes)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
