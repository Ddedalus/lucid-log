""" Utilities used by multiple examples."""


def worker(x):
    return x["text"]


async def generate_logs(logger):
    for i in range(10):
        x = dict()
        logger.warning("Generating log", extra={"iteration": i})
        try:
            worker(x)
        except Exception as e:
            logger.error("Error", exc_info=e, extra={"test": "test"})
