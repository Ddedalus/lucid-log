import asyncio
import logging
import sys
import json

# Configure the logging settings to log to stdout
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
        }
        return json.dumps(log_data)

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
            logger.exception(e, extra={"test": "test"})
        await asyncio.sleep(2)

async def main():
    await generate_logs()

if __name__ == "__main__":
    asyncio.run(main())