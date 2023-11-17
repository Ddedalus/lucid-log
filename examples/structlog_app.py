import structlog

from examples.shared import generate_logs

structlog.configure(
    [
        structlog.processors.add_log_level,
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.getLogger()

if __name__ == "__main__":
    generate_logs(logger)
    print("Unstructured nonsense!")
