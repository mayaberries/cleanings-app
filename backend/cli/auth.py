import httpx
import typer

from cli.config import save_session, clear_session, load_session, DEFAULT_API_BASE_URL
from cli.utils import fix_mojibake

app = typer.Typer(help="Authenticate the CLI against a backend deployment.")


def _post_json(url: str, payload: dict) -> httpx.Response:
    try:
        return httpx.post(url, json=payload)
    except UnicodeEncodeError:
        typer.secho(
            "Couldn't encode what you typed -- this usually means your terminal's "
            "locale isn't UTF-8 (check `echo $LANG`; try `export LANG=en_US.UTF-8`). "
            "Try again, avoiding accented characters or pasted smart quotes for now.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)


@app.command()
def login(
    api_base_url: str = typer.Option(DEFAULT_API_BASE_URL, prompt="Backend API base URL"),
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    """Logs in via the existing /users/login/token endpoint."""
    email = fix_mojibake(email)
    password = fix_mojibake(password)

    response = _post_json(
        f"{api_base_url.rstrip('/')}/users/login/token",
        {"username": email, "password": password},
    ) if False else httpx.post(  # login uses form data, not json -- see note below
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
def bootstrap(
    api_base_url: str = typer.Option(DEFAULT_API_BASE_URL, prompt="Backend API base URL"),
    email: str = typer.Option(..., prompt=True),
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
) -> None:
    """
    One-time setup: registers the platform's first superuser and logs the
    CLI in as them immediately. Only works while zero superusers exist --
    the backend enforces that (see ix_users_single_superuser).
    """
    email = fix_mojibake(email)
    username = fix_mojibake(username)
    password = fix_mojibake(password)

    response = _post_json(
        f"{api_base_url.rstrip('/')}/users/bootstrap-superuser/",
        {"email": email, "username": username, "password": password},
    )
    if response.status_code == 403:
        typer.secho("A superuser already exists. Ask them to log in and grant you access.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if response.status_code != 201:
        typer.secho(f"Bootstrap failed: {response.text}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    token = response.json()["access_token"]["access_token"]
    save_session(api_base_url=api_base_url.rstrip("/"), token=token)
    typer.secho("Superuser created and logged in.", fg=typer.colors.GREEN)


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