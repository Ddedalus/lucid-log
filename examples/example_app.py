import asyncio
import logging
import sys
import json
import traceback

# Configure the logging settings to log to stdout
# Configure the logging settings with a custom JSON formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'stack_trace': None
        }

        if record.exc_info:
            log_data['stack_trace'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

    def formatException(self, exc_info):
        exc_type, exc_value, exc_traceback = exc_info
        formatted_exception = traceback.format_exception(exc_type, exc_value, exc_traceback)
        return formatted_exception

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]

async def generate_logs():
    while True:
        x = dict()
        logger.info("Generating log")
        try:
            y = x["test"]
        except Exception as e:
            logger.error("Error", exc_info=e, extra={"test": "test"})
        await asyncio.sleep(2)

async def main():
    await generate_logs()

if __name__ == "__main__":
    asyncio.run(main())