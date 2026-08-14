import httpx
import typer

from cli.config import save_session, clear_session, load_session

app = typer.Typer(help="Authenticate the CLI against a backend deployment.")


@app.command()
def login(
    api_base_url: str = typer.Option(..., prompt="Backend API base URL (e.g. https://api.yourdomain.com/api)"),
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    """
    Logs in via the existing /users/login/token endpoint -- no separate
    auth path for the CLI. The account used here must have is_superuser
    set (see scripts/promote_superuser.py); a regular clinic_admin token
    works too but `clinics list` / `sites generate-all` will 403.
    """
    response = httpx.post(
        f"{api_base_url.rstrip('/')}/users/login/token",
        data={"username": email, "password": password},
    )
    if response.status_code != 200:
        typer.secho(f"Login failed: {response.text}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    token = response.json()["access_token"]
    save_session(api_base_url=api_base_url.rstrip("/"), token=token)
    typer.secho("Logged in.", fg=typer.colors.GREEN)


@app.command()
def logout() -> None:
    clear_session()
    typer.echo("Logged out.")


@app.command()
def whoami() -> None:
    session = load_session()
    if not session:
        typer.echo("Not logged in.")
        raise typer.Exit(code=1)
    typer.echo(f"Backend: {session['api_base_url']}")
