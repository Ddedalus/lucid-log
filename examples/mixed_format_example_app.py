import asyncio
import logging
from random import randint
import sys
import json
import traceback

# Configure the logging settings to log to stdout
class JsonFormatter(logging.Formatter):
    
    def format(self, record):
        if randint(0, 1) == 0:
            return super().format(record)
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

class StringLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        print(f"String Log: {log_entry}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

json_handler = logging.StreamHandler(sys.stdout)
json_handler.setFormatter(JsonFormatter())

string_handler = StringLogHandler()
string_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(json_handler)
logger.addHandler(string_handler)
async def generate_logs():
    while True:
        x = dict()
        logger.info("Generating log")
        try:
            y = x["test"]
        except Exception as e:
            logger.exception(e, extra={"test": "test"})
        await asyncio.sleep(2)

async def main():
    await generate_logs()

if __name__ == "__main__":
    asyncio.run(main())