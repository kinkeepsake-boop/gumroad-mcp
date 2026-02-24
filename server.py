import os
import httpx
from fastmcp import FastMCP

# ----------------------------
# Config
# ----------------------------
GUMROAD_TOKEN = os.getenv("GUMROAD_TOKEN")
if not GUMROAD_TOKEN:
    raise RuntimeError("Missing env var GUMROAD_TOKEN")

GUMROAD_API_BASE = "https://api.gumroad.com"

mcp = FastMCP("gumroad-mcp")


# ----------------------------
# Gumroad helpers
# Gumroad uses access_token as a query param.
# ----------------------------
async def gumroad_get(path: str, params: dict | None = None):
    params = params or {}
    params["access_token"] = GUMROAD_TOKEN

    url = f"{GUMROAD_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


async def gumroad_post(path: str, data: dict | None = None):
    data = data or {}
    data["access_token"] = GUMROAD_TOKEN

    url = f"{GUMROAD_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=data)
        r.raise_for_status()
        return r.json()


# ----------------------------
# MCP tools (read-only)
# ----------------------------
@mcp.tool()
async def list_sales(page: int = 1):
    """
    List recent sales. page starts at 1.
    """
    return await gumroad_get("/v2/sales", {"page": page})


@mcp.tool()
async def list_products():
    """
    List products for the authenticated Gumroad account.
    """
    return await gumroad_get("/v2/products")


@mcp.tool()
async def get_product(product_id: str):
    """
    Get a single product by ID (from list_products).
    """
    # Gumroad doesn't have a universal "get product" endpoint in all docs;
    # this is a common pattern: filter client-side by listing products.
    products = await gumroad_get("/v2/products")
    if not products.get("success"):
        return products
    for p in products.get("products", []):
        if str(p.get("id")) == str(product_id):
            return {"success": True, "product": p}
    return {"success": False, "error": f"Product not found: {product_id}"}


@mcp.tool()
async def sales_summary(pages: int = 1):
    """
    Quick summary across N pages of sales: count + gross totals (if present in payload).
    """
    total_count = 0
    total_amount_cents = 0

    for page in range(1, max(1, pages) + 1):
        data = await gumroad_get("/v2/sales", {"page": page})
        if not data.get("success"):
            return data

        sales = data.get("sales", []) or []
        total_count += len(sales)

        # Gumroad payload fields vary; try common ones safely
        for s in sales:
            for key in ("price", "amount", "total", "price_cents", "amount_cents", "total_cents"):
                v = s.get(key)
                if isinstance(v, int):
                    total_amount_cents += v
                    break

    return {
        "success": True,
        "pages": pages,
        "sale_count": total_count,
        "total_amount_cents_guess": total_amount_cents,
        "note": "Total is a best-effort sum based on available fields in the sale payload.",
    }


# ----------------------------
# Entrypoint: run MCP over HTTP for remote clients (ChatGPT)
# Endpoint will be available at: https://<domain>/mcp
# ----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    mcp.run(transport="http", host="0.0.0.0", port=port)run()
