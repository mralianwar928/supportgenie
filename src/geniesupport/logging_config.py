# logging_config.py  (structured JSON logs — reused pattern from Project #3)
import logging, json, sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {"level": record.levelname, "logger": record.name,
               "message": record.getMessage()}
        for key in ("latency_ms", "escalated", "cost_usd", "session"):
            if hasattr(record, key):
                log[key] = getattr(record, key)
        return json.dumps(log)

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
    return logging.getLogger("supportgenie")