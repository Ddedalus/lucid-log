import asyncio
import json
import logging
import sys
import traceback
from typing import Any

from examples.shared import generate_logs


# Configure the logging settings to log to stdout
# Configure the logging settings with a custom JSON formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["stack_trace"] = self._format_exception(record.exc_info)

        return json.dumps(log_data)

    def _format_exception(self, ei):
        exc_type, exc_value, exc_traceback = ei
        formatted_exception = traceback.format_exception(
            exc_type, exc_value, exc_traceback
        )
        return formatted_exception


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]


async def main():
    await generate_logs(logger)


if __name__ == "__main__":
    asyncio.run(main())
