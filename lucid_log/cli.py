import json
from pathlib import Path
from typing import Annotated, Any, Optional

import structlog
import typer

from lucid_log.rich_traceback_formatter import RichJsonTracebackFormatter

app = typer.Typer()


@app.command()
def help():
    print("TBD")


@app.command()
def show(log_file: Annotated[Optional[Path], typer.Argument()] = None):
    if log_file is None:
        typer.secho("Parsing logs from standard input...", fg=typer.colors.GREEN)
        while True:
            try:
                line = input()
            except EOFError:
                return
            display_line(line)

    with log_file.open() as file:
        for line in file.readlines():
            display_line(line)


logger = structlog.getLogger()

formatter = RichJsonTracebackFormatter()
renderer = structlog.dev.ConsoleRenderer(
    exception_formatter=formatter,  # type: ignore
)


def transform_exception_format(data: dict[str, Any]):
    exception = data.pop("exception", None)
    if not exception:
        return data
    data["exc_info"] = (
        exception[0]["exc_type"],
        exception[0]["exc_value"],
        exception[0]["frames"],
    )
    return data


def display_line(line: str):
    try:
        data = json.loads(line)
        data = transform_exception_format(data)
        print(renderer(logger, "wut", data))
    except json.JSONDecodeError:
        typer.secho(f"> {line}", fg=typer.colors.BRIGHT_BLACK)
