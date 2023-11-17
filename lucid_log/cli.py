import json
import sys
from pathlib import Path
from typing import Annotated, Any, Optional

import loguru
import typer
from rich import print

from lucid_log.aws_log_parser import LucidAWSLogs
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


@app.command()
def aws(
    log_group_name: Annotated[str, typer.Argument()],
    log_stream_pattern: Annotated[Optional[str], typer.Argument()] = "ALL",
    region: Optional[str] = typer.Option(None, "--region", "-r", envvar="AWS_REGION"),
    watch: bool = typer.Option(False, "--watch", "-w"),
):
    typer.secho("Parsing logs from cloudwatch...", fg=typer.colors.GREEN)
    parser = LucidAWSLogs.get_parser(log_group_name, log_stream_pattern, region)
    # Get each log line from the generator, if no logs remain, break unless watching
    for line in parser:  # type: ignore
        if line:
            display_line(line)
        else:
            if not watch:
                break


formatter = RichJsonTracebackFormatter()


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
        # TODO: We can print directly with Rich and not depend on loguru for this
        loguru.logger.log(data.pop("level").upper(), data.pop("event"), **data)

        if exc_info := data.pop("exc_info", None):
            formatter(sys.stderr, exc_info)

    except json.JSONDecodeError:
        typer.secho(f"> {line}", fg=typer.colors.BRIGHT_BLACK)
