""" Console renderer for structured log events. """

import json
import sys
from typing import Any

import loguru
from rich import print

from lucid_log.traceback_formatter import RichJsonTracebackFormatter

trackeback_formatter = RichJsonTracebackFormatter()


def render_log(log: str):
    """Display a single log entry in the console."""
    try:
        data = json.loads(log)
    except json.JSONDecodeError:
        return print(f"[red]>[/red] [bright_black]{log}[/bright_black]")

    # TODO: add data validation
    exc_info = extract_exception_info(data)
    # TODO: We can print directly with Rich and not depend on loguru for this
    loguru.logger.log(data.pop("level").upper(), data.pop("event"), **data)

    if exc_info:
        trackeback_formatter(sys.stderr, exc_info)


def extract_exception_info(data: dict[str, Any]):
    if exception := data.pop("exception", None):
        return (
            exception[0]["exc_type"],
            exception[0]["exc_value"],
            exception[0]["frames"],
        )
