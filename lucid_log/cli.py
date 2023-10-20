import typer

app = typer.Typer()


@app.command()
def help():
    print("TBD")


@app.command()
def show():
    print("Hello!")
