"""
Bridges the backend (source of truth for which clinics/keys exist) to the
Node/Astro generator (frontend/scripts/generate-site.mjs). This module
never touches Astro itself -- it just resolves clinic config over HTTP and
shells out, same contract the generator already exposes on the CLI.
"""
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from cli.client import get_client, die_on_error

app = typer.Typer(help="Generate static clinic booking sites from the Astro template.")

# backend/cli/sites.py -> repo root -> frontend/scripts/generate-site.mjs
REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATE_SCRIPT = REPO_ROOT / "frontend" / "scripts" / "generate-site.mjs"


def _resolve_live_public_key(client, clinic_id: str) -> str:
    response = client.get(f"/clinics/{clinic_id}/api-keys/")
    die_on_error(response)
    keys = response.json()
    live_keys = [k for k in keys if k["environment"] == "live" and k["is_active"]]
    if not live_keys:
        typer.secho(
            f"Clinic {clinic_id} has no active live API key. "
            f"Create one first (POST /clinics/{clinic_id}/api-keys/).",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    # Most-recently-created active live key -- list is already ordered by
    # created_at DESC (see LIST_KEYS_FOR_CLINIC_QUERY).
    return live_keys[0]["public_key"]


def _run_generator(*, slug: str, clinic_id: str, key: str, api_url: str, name: str) -> None:
    if not GENERATE_SCRIPT.exists():
        typer.secho(f"Generator script not found at {GENERATE_SCRIPT}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    result = subprocess.run(
        [
            "node", str(GENERATE_SCRIPT),
            "--slug", slug,
            "--clinic-id", clinic_id,
            "--key", key,
            "--api-url", api_url,
            "--name", name,
        ],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        typer.secho(f"Site generation failed for '{slug}' (exit {result.returncode})", fg=typer.colors.RED)
        raise typer.Exit(code=result.returncode)


@app.command()
def generate(
    clinic_id: str,
    public_api_url: str = typer.Option(..., help="Base URL the *generated site* will call at runtime, e.g. https://api.yourdomain.com/api"),
) -> None:
    """Fetch one clinic's config from the backend and build its static site."""
    with get_client() as client:
        clinic_response = client.get(f"/clinics/{clinic_id}/")
        die_on_error(clinic_response)
        clinic = clinic_response.json()

        public_key = _resolve_live_public_key(client, clinic_id)

    _run_generator(
        slug=clinic["slug"], clinic_id=clinic["id"], key=public_key,
        api_url=public_api_url, name=clinic["name"],
    )
    typer.secho(f"✓ built frontend/sites/{clinic['slug']}/", fg=typer.colors.GREEN)


@app.command("generate-all")
def generate_all(
    public_api_url: str = typer.Option(..., help="Base URL every generated site will call at runtime"),
    skip_missing_keys: bool = typer.Option(
        True, help="Skip clinics with no active live key instead of aborting the whole batch"
    ),
) -> None:
    """
    Walk every clinic (GET /clinics/, superuser-only) and (re)build its
    site. This is the command to run after a template change, since config
    is baked in at build time and nothing rebuilds itself automatically.
    """
    with get_client() as client:
        clinics_response = client.get("/clinics/", params={"limit": 500})
        die_on_error(clinics_response)
        clinics = clinics_response.json()

        built, skipped = 0, 0
        for clinic in clinics:
            try:
                public_key = _resolve_live_public_key(client, clinic["id"])
            except typer.Exit:
                if skip_missing_keys:
                    typer.secho(f"  skipping {clinic['slug']} (no active live key)", fg=typer.colors.YELLOW)
                    skipped += 1
                    continue
                raise

            _run_generator(
                slug=clinic["slug"], clinic_id=clinic["id"], key=public_key,
                api_url=public_api_url, name=clinic["name"],
            )
            built += 1

    typer.secho(f"✓ built {built} site(s), skipped {skipped}", fg=typer.colors.GREEN)
