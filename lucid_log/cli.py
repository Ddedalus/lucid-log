from pathlib import Path
from typing import Annotated, Optional

import typer

from lucid_log.aws_log_parser import LucidAWSLogs
from lucid_log.renderer import render_log

app = typer.Typer()


@app.command()
def help():
    typer.echo("TBD")


@app.command()
def show(log_file: Annotated[Optional[Path], typer.Argument()] = None):
    if log_file is None:
        typer.secho("Parsing logs from standard input...", fg=typer.colors.GREEN)
        while True:
            try:
                line = input()
            except EOFError:
                return
            render_log(line)

    with log_file.open() as file:
        for line in file.readlines():
            render_log(line)


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
            render_log(line)
        elif not watch:
            break
