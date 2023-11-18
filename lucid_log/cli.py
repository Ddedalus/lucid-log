from pathlib import Path
from typing import Annotated, Optional

import typer

from lucid_log.aws_log_parser import AWSLogConfig, LucidAWSLogs
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
    log_group_name: Annotated[Optional[str], typer.Argument()] = None,
    log_stream_pattern: Annotated[Optional[str], typer.Argument()] = "ALL",
    region: Optional[str] = typer.Option(None, "--region", "-r", envvar="AWS_REGION"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c"),
    watch: bool = typer.Option(False, "--watch", "-w"),
):
    typer.secho("Parsing logs from cloudwatch...", fg=typer.colors.GREEN)
    try:
        config_kwargs = LucidAWSLogs.parse_config_file(config_file)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    args = {
        "log_group_name": log_group_name,
        "aws_region": region,
        "log_stream_name": log_stream_pattern,
    }
    args.update(config_kwargs)
    config = AWSLogConfig(**args)
    if config.log_group_name is None:
        typer.secho("Error: No log group name specified", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    parser = LucidAWSLogs.get_parser(**config.dict())
    # Get each log line from the generator, if no logs remain, break unless watching
    for line in parser:  # type: ignore
        if line:
            render_log(line)
        elif not watch:
            break
