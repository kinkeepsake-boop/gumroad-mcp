import os
import httpx
from mcp.server.fastmcp import FastMCP

GUMROAD_TOKEN = os.environ["GUMROAD_TOKEN"]

mcp = FastMCP("gumroad")

async def gumroad_get(path: str, params=None):
    params = params or {}
    params["access_token"] = GUMROAD_TOKEN

    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.gumroad.com{path}", params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def list_sales(page: int = 1):
    return await gumroad_get("/v2/sales", {"page": page})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
