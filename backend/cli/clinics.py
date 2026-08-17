from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cli.client import get_client, die_on_error

app = typer.Typer(help="Inspect clinics across the whole platform (requires a superuser session).")
console = Console()


@app.command("list")
def list_clinics(limit: int = 100, offset: int = 0) -> None:
    """Calls GET /clinics/ -- the superuser-only listing endpoint."""
    with get_client() as client:
        response = client.get("/clinics/", params={"limit": limit, "offset": offset})
    die_on_error(response)

    clinics = response.json()
    table = Table(title=f"Clinics ({len(clinics)})")
    table.add_column("Slug")
    table.add_column("Name")
    table.add_column("ID")
    for clinic in clinics:
        table.add_row(clinic["slug"], clinic["name"], clinic["id"])
    console.print(table)


@app.command()
def keys(clinic_id: str) -> None:
    """Calls GET /clinics/{clinic_id}/api-keys/ -- works for any clinic
    when the session is a superuser, thanks to the is_superuser bypass in
    check_clinic_admin_permissions."""
    with get_client() as client:
        response = client.get(f"/clinics/{clinic_id}/api-keys/")
    die_on_error(response)

    table = Table(title=f"API keys for {clinic_id}")
    table.add_column("Label")
    table.add_column("Environment")
    table.add_column("Public key")
    table.add_column("Active")
    for key in response.json():
        table.add_row(key.get("label") or "-", key["environment"], key["public_key"], str(key["is_active"]))
    console.print(table)


@app.command("create")
def create_clinic(
        name: str,
        email: Optional[str] = typer.Option(None),
        phone: Optional[str] = typer.Option(None, "--phone"),
        address: Optional[str] = typer.Option(None),
        slug: Optional[str] = typer.Option(None, help="Defaults to a slugified version of the name"),
) -> None:
    """
    Calls POST /clinics/ and links the new clinic to your own (logged-in)
    user -- same as the normal clinic_admin signup flow. Only works once
    per user (see the note in create_clinic_for_admin) since it attaches
    clinic_id to whoever's logged in.
    """
    payload = {"name": name}
    if email:
        payload["email"] = email
    if phone:
        payload["phone_number"] = phone
    if address:
        payload["address"] = address
    if slug:
        payload["slug"] = slug

    with get_client() as client:
        response = client.post("/clinics/", json=payload)
    die_on_error(response)

    clinic = response.json()
    typer.secho(
        f"✓ created clinic '{clinic['name']}' (slug: {clinic['slug']}, id: {clinic['id']})",
        fg=typer.colors.GREEN,
    )


@app.command("create-key")
def create_key(
    clinic_id: str,
    label: Optional[str] = typer.Option(None, help="e.g. 'Website widget'"),
    environment: str = typer.Option("live", help="'live' or 'test'"),
) -> None:
    """
    Calls POST /clinics/{clinic_id}/api-keys/. This is the key
    `sites generate` / `generate-all` picks up automatically (they always
    use the most recent active 'live' key), so this is the missing piece
    between `clinics create` and `sites generate`.
    """
    payload = {"environment": environment}
    if label:
        payload["label"] = label

    with get_client() as client:
        response = client.post(f"/clinics/{clinic_id}/api-keys/", json=payload)
    die_on_error(response)

    key = response.json()
    typer.secho(f"✓ created {key['environment']} key: {key['public_key']}", fg=typer.colors.GREEN)
    typer.echo("Not a secret — safe to re-fetch any time with `clinics keys <clinic_id>`.")