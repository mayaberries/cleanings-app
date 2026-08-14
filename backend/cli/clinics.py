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
