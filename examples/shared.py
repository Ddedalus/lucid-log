""" Utilities used by multiple examples."""


def worker(x):
    return x["text"]


def nested_worker(x):
    try:
        return worker(x)
    except Exception as e:
        raise ValueError("Outer exception") from e


def generate_logs(logger):
    for i in range(2):
        logger.warning("Generating log", extra={"iteration": i})
        try:
            worker({})
        except Exception:
            logger.exception("Error", extra={"test": "test"})

    try:
        nested_worker({})
    except Exception:
        logger.exception("Nested error", extra={"test": "test"})
        import sys

        e, v, trace = sys.exc_info()
        assert v
        assert v.__cause__
        print(getattr(v, "__cause__").__traceback__)
