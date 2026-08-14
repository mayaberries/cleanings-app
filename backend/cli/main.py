import typer

from cli import auth, clinics, sites

app = typer.Typer(help="Platform admin CLI: manage clinics and generate their static booking sites.")
app.add_typer(auth.app, name="auth")
app.add_typer(clinics.app, name="clinics")
app.add_typer(sites.app, name="sites")

# Flatten the most common auth commands to the top level for convenience,
# so `admin login` works instead of only `admin auth login`.
app.command(name="login")(auth.login)
app.command(name="logout")(auth.logout)


if __name__ == "__main__":
    app()
