"""Standards-compatible MCP stdio server for trusted host applications."""

from mcp.server.fastmcp import FastMCP

from app.database import AsyncSessionLocal
from app.mcp import tools

mcp = FastMCP("GennomX AI", instructions="Read-only biomedical intelligence tools with evidence.")


async def _call(handler, arguments: dict) -> dict:
    async with AsyncSessionLocal() as db:
        return await handler(arguments, db=db)


@mcp.tool()
async def search_drugs(arguments: dict) -> dict:
    return await _call(tools.search_drugs, arguments)


@mcp.tool()
async def find_trials(arguments: dict) -> dict:
    return await _call(tools.find_trials, arguments)


@mcp.tool()
async def compare_assets(arguments: dict) -> dict:
    return await _call(tools.compare_assets, arguments)


@mcp.tool()
async def get_company_pipeline(arguments: dict) -> dict:
    return await _call(tools.get_company_pipeline, arguments)


@mcp.tool()
async def get_trial_results(arguments: dict) -> dict:
    return await _call(tools.get_trial_results, arguments)


@mcp.tool()
async def search_publications(arguments: dict) -> dict:
    return await _call(tools.search_publications, arguments)


@mcp.tool()
async def get_regulatory_status(arguments: dict) -> dict:
    return await _call(tools.get_regulatory_status, arguments)


@mcp.tool()
async def build_report_data_bundle(arguments: dict) -> dict:
    return await _call(tools.build_report_data_bundle, arguments)


@mcp.tool()
async def fetch_source_evidence(arguments: dict) -> dict:
    return await _call(tools.fetch_source_evidence, arguments)


if __name__ == "__main__":
    mcp.run(transport="stdio")
