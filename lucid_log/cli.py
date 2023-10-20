import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print_json

app = typer.Typer()


@app.command()
def help():
    print("TBD")


@app.command()
def show(log_file: Annotated[Optional[Path], typer.Argument()] = None):
    if log_file is None:
        typer.secho("Parsing logs from standard input...", fg=typer.colors.GREEN)
        while True:
            line = input()
            display_line(line)

    with log_file.open() as file:
        for line in file.readlines():
            display_line(line)


def display_line(line: str):
    try:
        data = json.loads(line)
        print_json(data=data)
    except json.JSONDecodeError:
        typer.secho(f"> {line}", fg=typer.colors.BRIGHT_BLACK)
