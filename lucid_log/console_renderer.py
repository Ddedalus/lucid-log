from types import TracebackType
from typing import Callable, Protocol, TextIO


class _Styles(Protocol):
    reset: str
    bright: str
    level_critical: str
    level_exception: str
    level_error: str
    level_warn: str
    level_info: str
    level_debug: str
    level_notset: str

    timestamp: str
    logger_name: str
    kv_key: str
    kv_value: str


Styles = _Styles | type[_Styles]
ExcInfo = tuple[type[BaseException], BaseException, TracebackType | None]
ExceptionRenderer = Callable[[TextIO, ExcInfo], None]


class ConsoleRenderer:
    """
    Render ``event_dict`` nicely aligned, possibly in colors, and ordered.

    If ``event_dict`` contains a true-ish ``exc_info`` key, it will be rendered
    *after* the log line. If Rich_ or better-exceptions_ are present, in colors
    and with extra context.

    Arguments:

        pad_event: Pad the event to this many characters.

        colors:
            Use colors for a nicer output. `True` by default. On Windows only
            if Colorama_ is installed.

        force_colors:
            Force colors even for non-tty destinations. Use this option if your
            logs are stored in a file that is meant to be streamed to the
            console. Only meaningful on Windows.

        repr_native_str:
            When `True`, `repr` is also applied to native strings (i.e. unicode
            on Python 3 and bytes on Python 2). Setting this to `False` is
            useful if you want to have human-readable non-ASCII output on
            Python 2.  The ``event`` key is *never* `repr` -ed.

        level_styles:
            When present, use these styles for colors. This must be a dict from
            level names (strings) to Colorama styles. The default can be
            obtained by calling `ConsoleRenderer.get_default_level_styles`

        exception_formatter:
            A callable to render ``exc_infos``. If Rich_ or better-exceptions_
            are installed, they are used for pretty-printing by default (rich_
            taking precedence). You can also manually set it to
            `plain_traceback`, `better_traceback`, an instance of
            `RichTracebackFormatter` like `rich_traceback`, or implement your
            own.

        sort_keys: Whether to sort keys when formatting. `True` by default.

        event_key:
            The key to look for the main log message. Needed when you rename it
            e.g. using `structlog.processors.EventRenamer`.

        timestamp_key:
            The key to look for timestamp of the log message. Needed when you
            rename it e.g. using `structlog.processors.EventRenamer`.

    Requires the Colorama_ package if *colors* is `True` **on Windows**.

    .. _Colorama: https://pypi.org/project/colorama/
    .. _better-exceptions: https://pypi.org/project/better-exceptions/
    .. _Rich: https://pypi.org/project/rich/

    .. versionadded:: 16.0.0
    .. versionadded:: 16.1.0 *colors*
    .. versionadded:: 17.1.0 *repr_native_str*
    .. versionadded:: 18.1.0 *force_colors*
    .. versionadded:: 18.1.0 *level_styles*
    .. versionchanged:: 19.2.0
       Colorama now initializes lazily to avoid unwanted initializations as
       ``ConsoleRenderer`` is used by default.
    .. versionchanged:: 19.2.0 Can be pickled now.
    .. versionchanged:: 20.1.0
       Colorama does not initialize lazily on Windows anymore because it breaks
       rendering.
    .. versionchanged:: 21.1.0
       It is additionally possible to set the logger name using the
       ``logger_name`` key in the ``event_dict``.
    .. versionadded:: 21.2.0 *exception_formatter*
    .. versionchanged:: 21.2.0
       `ConsoleRenderer` now handles the ``exc_info`` event dict key itself. Do
       **not** use the `structlog.processors.format_exc_info` processor
       together with `ConsoleRenderer` anymore! It will keep working, but you
       can't have customize exception formatting and a warning will be raised
       if you ask for it.
    .. versionchanged:: 21.2.0
       The colors keyword now defaults to True on non-Windows systems, and
       either True or False in Windows depending on whether Colorama is
       installed.
    .. versionadded:: 21.3.0 *sort_keys*
    .. versionadded:: 22.1.0 *event_key*
    .. versionadded:: 23.2.0 *timestamp_key*
    """

    def __init__(
        self,
        exception_formatter: ExceptionRenderer,
        pad_event: int = 30,
        colors: bool = True,
        force_colors: bool = False,
        repr_native_str: bool = False,
        level_styles: Styles | None = None,
        sort_keys: bool = True,
        event_key: str = "event",
        timestamp_key: str = "timestamp",
    ):
        if colors:
            styles = _ColorfulStyles
        else:
            styles = _PlainStyles

        self._styles = styles
        self._pad_event = pad_event

        if level_styles is None:
            self._level_to_color = self.get_default_level_styles(colors)
        else:
            self._level_to_color = level_styles

        for key in self._level_to_color:
            self._level_to_color[key] += styles.bright
        self._longest_level = len(
            max(self._level_to_color.keys(), key=lambda e: len(e))
        )

        self._repr_native_str = repr_native_str
        self._exception_formatter = exception_formatter
        self._sort_keys = sort_keys
        self._event_key = event_key
        self._timestamp_key = timestamp_key

    def _repr(self, val: Any) -> str:
        """
        Determine representation of *val* depending on its type &
        self._repr_native_str.
        """
        if self._repr_native_str is True:
            return repr(val)

        if isinstance(val, str):
            return val

        return repr(val)

    def __call__(  # noqa: PLR0912
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> str:
        sio = StringIO()

        ts = event_dict.pop(self._timestamp_key, None)
        if ts is not None:
            sio.write(
                # can be a number if timestamp is UNIXy
                self._styles.timestamp
                + str(ts)
                + self._styles.reset
                + " "
            )
        level = event_dict.pop("level", None)
        if level is not None:
            sio.write(
                "["
                + self._level_to_color.get(level, "")
                + _pad(level, self._longest_level)
                + self._styles.reset
                + "] "
            )

        # force event to str for compatibility with standard library
        event = event_dict.pop(self._event_key, None)
        if not isinstance(event, str):
            event = str(event)

        if event_dict:
            event = _pad(event, self._pad_event) + self._styles.reset + " "
        else:
            event += self._styles.reset
        sio.write(self._styles.bright + event)

        logger_name = event_dict.pop("logger", None)
        if logger_name is None:
            logger_name = event_dict.pop("logger_name", None)

        if logger_name is not None:
            sio.write(
                "["
                + self._styles.logger_name
                + self._styles.bright
                + logger_name
                + self._styles.reset
                + "] "
            )

        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)
        exc_info = event_dict.pop("exc_info", None)

        event_dict_keys: Iterable[str] = event_dict.keys()
        if self._sort_keys:
            event_dict_keys = sorted(event_dict_keys)

        sio.write(
            " ".join(
                self._styles.kv_key
                + key
                + self._styles.reset
                + "="
                + self._styles.kv_value
                + self._repr(event_dict[key])
                + self._styles.reset
                for key in event_dict_keys
            )
        )

        if stack is not None:
            sio.write("\n" + stack)
            if exc_info or exc is not None:
                sio.write("\n\n" + "=" * 79 + "\n")

        if exc_info:
            exc_info = _figure_out_exc_info(exc_info)

            if exc_info != (None, None, None):
                self._exception_formatter(sio, exc_info)
        elif exc is not None:
            if self._exception_formatter is not plain_traceback:
                warnings.warn(
                    "Remove `format_exc_info` from your processor chain "
                    "if you want pretty exceptions.",
                    stacklevel=2,
                )
            sio.write("\n" + exc)

        return sio.getvalue()

    @staticmethod
    def get_default_level_styles(colors: bool = True) -> Any:
        """
        Get the default styles for log levels

        This is intended to be used with `ConsoleRenderer`'s ``level_styles``
        parameter.  For example, if you are adding custom levels in your
        home-grown :func:`~structlog.stdlib.add_log_level` you could do::

            my_styles = ConsoleRenderer.get_default_level_styles()
            my_styles["EVERYTHING_IS_ON_FIRE"] = my_styles["critical"] renderer
            = ConsoleRenderer(level_styles=my_styles)

        Arguments:

            colors:
                Whether to use colorful styles. This must match the *colors*
                parameter to `ConsoleRenderer`. Default: `True`.
        """
        styles: Styles
        styles = _ColorfulStyles if colors else _PlainStyles
        return {
            "critical": styles.level_critical,
            "exception": styles.level_exception,
            "error": styles.level_error,
            "warn": styles.level_warn,
            "warning": styles.level_warn,
            "info": styles.level_info,
            "debug": styles.level_debug,
            "notset": styles.level_notset,
        }
