"""Entry point for fpl-mcp-v2.

Runs in two modes:
- ``python -m fpl_mcp``  → MCP server mode (stdio transport)
- ``python -m fpl_mcp <args>`` → CLI mode (setup, test, clear, server)
"""

from __future__ import annotations

import asyncio
import logging
import sys


def main() -> None:
    if len(sys.argv) > 1:
        # CLI mode: delegate to Typer CLI
        from fpl_mcp.cli import main as cli_main

        cli_main()
    else:
        # MCP server mode: bootstrap dependencies and run
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

        async def _run_server() -> None:
            from fpl_mcp.config import FPLConfig
            from fpl_mcp.server import FPLMCPServer, create_services

            config = FPLConfig()
            services = await create_services(config)
            server = FPLMCPServer(services, config)
            await server.run()

        try:
            asyncio.run(_run_server())
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
