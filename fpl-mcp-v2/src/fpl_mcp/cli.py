"""Command-line interface for FPL MCP v2.

Provides interactive setup, authentication testing, and server launch.
"""

from __future__ import annotations

import asyncio
import logging

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from fpl_mcp.config import FPLConfig
from fpl_mcp.infrastructure.auth_service import AuthenticationError, FPLAuthService
from fpl_mcp.infrastructure.credentials import SecureCredentialManager
from fpl_mcp.server import FPLMCPServer, create_services

app = typer.Typer(
    name="fpl-mcp-v2",
    help="Fantasy Premier League MCP Server v2",
    no_args_is_help=True,
)
console = Console()


def _print_banner() -> None:
    """Display the FPL MCP banner."""
    console.print(
        Panel.fit(
            "[bold cyan]Fantasy Premier League MCP v2[/bold cyan]\n"
            "[dim]Secure, fast, and maintainable FPL integration[/dim]",
            border_style="cyan",
        )
    )


@app.command()
def setup() -> None:
    """Interactive setup of FPL credentials using OS keyring."""
    _print_banner()
    console.print()
    console.print(
        "[bold yellow]Step 1:[/bold yellow] Obtain your FPL refresh token\n"
        "  1. Open Chrome and go to [link]https://fantasy.premierleague.com/[/link]\n"
        "  2. Log in with your FPL account\n"
        "  3. Open DevTools (F12) → Application (or Storage) tab\n"
        "  4. Navigate to Local Storage → https://fantasy.premierleague.com\n"
        "  5. Look for a key starting with [bold]oidc.user:[/bold]\n"
        "  6. Expand it and copy the [bold]refresh_token[/bold] value\n"
    )

    refresh_token = Prompt.ask(
        "[bold green]Paste your refresh token[/bold green]",
        password=True,
    )
    if not refresh_token or len(refresh_token) < 10:
        console.print("[bold red]Invalid refresh token. Setup aborted.[/bold red]")
        raise typer.Exit(1)

    team_id = Prompt.ask(
        "[bold green]Enter your FPL team ID[/bold green] "
        "(found in your team URL: fantasy.premierleague.com/entry/[bold]XXXXXX[/bold]/)",
    )
    if not team_id or not team_id.strip().isdigit():
        console.print("[bold red]Invalid team ID. Setup aborted.[/bold red]")
        raise typer.Exit(1)

    creds = SecureCredentialManager()
    creds.store_credentials(refresh_token.strip(), team_id.strip())
    console.print()
    console.print(
        "[bold green]✓ Credentials stored securely in OS keyring.[/bold green]"
    )

    # Run automatic test
    console.print()
    console.print("[bold blue]Running authentication test...[/bold blue]")
    try:
        asyncio.run(_test_auth())
    except Exception as exc:
        console.print(f"[bold red]Authentication test failed: {exc}[/bold red]")
        console.print(
            "[dim]Your credentials were saved, but the test failed. "
            "You can re-run 'fpl-mcp-config test' later.[/dim]"
        )


async def _test_auth() -> None:
    """Async helper to test authentication after setup."""
    config = FPLConfig()
    creds = SecureCredentialManager()
    import httpx

    http_client = httpx.AsyncClient()
    auth = FPLAuthService(
        http_client=http_client,
        credentials=creds,
        token_url=config.resolved_token_url,
        client_id=config.oidc_client_id,
    )
    try:
        token = await auth.authenticate()
        _, team_id_str = creds.load_credentials()
        if team_id_str:
            entry = await auth.get_entry_data(int(team_id_str))
            table = Table(title="Authentication Test Results", show_header=False)
            table.add_row("Status", "[bold green]✓ Success[/bold green]")
            table.add_row(
                "Token Expiry",
                token.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            )
            table.add_row(
                "Manager",
                entry.get("player_first_name", "")
                + " "
                + entry.get("player_last_name", ""),
            )
            table.add_row("Team Name", entry.get("name", "N/A"))
            table.add_row(
                "Overall Rank",
                str(entry.get("summary_overall_rank", "N/A")),
            )
            console.print(table)
        else:
            console.print(
                "[bold green]✓ Authentication succeeded, but no team_id found.[/bold green]"
            )
    except AuthenticationError as exc:
        console.print(f"[bold red]Authentication failed: {exc}[/bold red]")
        raise
    finally:
        await http_client.aclose()


@app.command()
def test() -> None:
    """Test FPL authentication."""
    _print_banner()
    console.print()
    try:
        asyncio.run(_test_auth())
    except Exception as exc:
        console.print(f"[bold red]Test failed: {exc}[/bold red]")
        raise typer.Exit(1)


@app.command()
def clear() -> None:
    """Clear stored credentials from OS keyring."""
    creds = SecureCredentialManager()
    if not creds.has_credentials():
        console.print("[yellow]No credentials found in keyring.[/yellow]")
        return

    confirm = Prompt.ask(
        "[bold red]Are you sure you want to delete all stored credentials?[/bold red]",
        choices=["y", "n"],
        default="n",
    )
    if confirm != "y":
        console.print("[dim]Cancelled.[/dim]")
        return

    creds.clear_credentials()
    console.print("[bold green]✓ Credentials cleared from OS keyring.[/bold green]")


@app.command()
def server() -> None:
    """Run the MCP server (stdio transport)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _print_banner()
    console.print("[bold blue]Initializing FPL MCP server...[/bold blue]")

    async def _run() -> None:
        config = FPLConfig()
        services = await create_services(config)
        fpl_server = FPLMCPServer(services, config)
        await fpl_server.run()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[dim]Server stopped.[/dim]")


def main() -> None:
    app()
