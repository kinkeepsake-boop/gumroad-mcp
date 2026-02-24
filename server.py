import os
import httpx
from fastmcp import FastMCP
from starlette.responses import PlainTextResponse

GUMROAD_TOKEN = os.getenv("GUMROAD_TOKEN")
if not GUMROAD_TOKEN:
    raise RuntimeError("Missing env var GUMROAD_TOKEN")

mcp = FastMCP("gumroad-mcp")

GUMROAD_API_BASE = "https://api.gumroad.com"


async def gumroad_get(path: str, params: dict | None = None):
    params = params or {}
    params["access_token"] = GUMROAD_TOKEN
    url = f"{GUMROAD_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def list_sales(page: int = 1):
    return await gumroad_get("/v2/sales", {"page": page})


@mcp.tool()
async def list_products():
    return await gumroad_get("/v2/products")


# Simple health check so you can verify the web server is responding.
@mcp.custom_route("/health", methods=["GET"])
async def health(_request):
    return PlainTextResponse("ok")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"Starting FastMCP HTTP on 0.0.0.0:{port} at /mcp/")
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp/",
    )
