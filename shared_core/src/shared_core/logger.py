import logging
import sys
import os
import structlog

def setup_logger(log_level: str = "INFO", app_name: str = "app"):
    """
    공통 로거 설정.
    ENVIRONMENT가 'production'이면 UTF-8 JSON 출력, 아니면 Console 출력.
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    env = os.getenv("ENVIRONMENT", "development")
    is_prod = env.lower() == "production"

    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
    ]

    if is_prod:
        processors.append(structlog.processors.JSONRenderer(ensure_ascii=False))
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log_level_upper = log_level.upper()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level_upper, logging.INFO),
    )

    return structlog.get_logger(app_name)

# 기본 로거 인스턴스
logger = structlog.get_logger()
