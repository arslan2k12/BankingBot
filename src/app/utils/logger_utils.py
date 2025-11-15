import structlog
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration with beautiful readable format for both console and file"""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create the beautiful formatter that matches banking agent format
    beautiful_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure structlog with readable format
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Use KeyValueRenderer for readable format instead of JSONRenderer
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Configure console logging with beautiful format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(beautiful_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified with same beautiful format
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(beautiful_formatter)  # Use same beautiful format for file
        file_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)
    
    # Set root logger level
    root_logger.setLevel(getattr(logging, log_level.upper()))

def get_logger(name: str):
    """Get a logger instance with beautiful readable format"""
    # Use standard logging for consistent beautiful format
    return logging.getLogger(name)
