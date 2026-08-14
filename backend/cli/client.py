"""
Thin httpx wrapper every command shares. The CLI is deliberately just an
HTTP client of the backend's own public/staff API -- no direct DB or
internal-module imports -- so it works unmodified against local, staging,
or production deployments, and never drifts from what the API actually
allows a superuser to do.
"""
import sys

import httpx
import typer

from cli.config import load_session


def get_client() -> httpx.Client:
    session = load_session()
    if not session:
        typer.secho("Not logged in. Run `admin login` first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    return httpx.Client(
        base_url=session["api_base_url"],
        headers={"Authorization": f"Bearer {session['token']}"},
        timeout=30.0,
    )


def die_on_error(response: httpx.Response) -> None:
    if response.status_code >= 400:
        typer.secho(f"Request failed ({response.status_code}): {response.text}", fg=typer.colors.RED)
        sys.exit(1)
