from __future__ import annotations

import shutil
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Literal, Sequence, TextIO

try:
    import rich
    from rich.console import Console
    from rich.traceback import Stack, Trace, Traceback
except ImportError:
    rich = None  # type: ignore[assignment]


@dataclass
class RichJsonTracebackFormatter:
    """
    A Rich traceback renderer that accepts json-serialized exceptions.

    Taken from structlog.dev implementation.

    Pass an instance as `ConsoleRenderer`'s ``exception_formatter`` argument.

    See :class:`rich.traceback.Traceback` for details on the arguments.

    If a *width* of -1 is passed, the terminal width is used. If the width
    can't be determined, fall back to 80.
    """

    color_system: Literal[
        "auto", "standard", "256", "truecolor", "windows"
    ] = "truecolor"
    show_locals: bool = True
    max_frames: int = 100
    theme: str | None = None
    word_wrap: bool = False
    extra_lines: int = 3
    width: int = 100
    indent_guides: bool = True
    locals_max_length: int = 10
    locals_max_string: int = 80
    locals_hide_dunder: bool = True
    locals_hide_sunder: bool = False
    suppress: Sequence[str | ModuleType] = ()

    def __call__(self, sio: TextIO, exc_info: dict[str, Any]) -> None:
        if self.width == -1:
            self.width, _ = shutil.get_terminal_size((80, 0))

        sio.write("\n")
        trace = Trace(stacks=[])
        Console(file=sio, color_system=self.color_system).print(
            Traceback(
                trace=trace,
                show_locals=self.show_locals,
                max_frames=self.max_frames,
                theme=self.theme,
                word_wrap=self.word_wrap,
                extra_lines=self.extra_lines,
                width=self.width,
                indent_guides=self.indent_guides,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
                locals_hide_dunder=self.locals_hide_dunder,
                locals_hide_sunder=self.locals_hide_sunder,
                suppress=self.suppress,
            )
        )
