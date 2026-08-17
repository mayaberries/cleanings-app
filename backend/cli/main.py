import typer

from cli import auth, clinics, sites

app = typer.Typer(help="Platform admin CLI: manage clinics and generate their static booking sites.")
app.add_typer(auth.app, name="auth")
app.add_typer(clinics.app, name="clinics")
app.add_typer(sites.app, name="sites")

app.command(name="login")(auth.login)
app.command(name="bootstrap")(auth.bootstrap)
app.command(name="logout")(auth.logout)

if __name__ == "__main__":
    app()
