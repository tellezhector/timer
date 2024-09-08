
import logging

import logging.handlers

def log_to_file(path: str):
    """Sets a log file handler.
    
    Args:
        path: path to the file to log to.
    """
    rotating_file_handler = logging.handlers.RotatingFileHandler(
            filename=path, 
            mode='a',
            maxBytes=128*1024*1024, # 128 MB
            backupCount=2,
            encoding='utf-8',
            delay=0
        )
    logging.basicConfig(
        encoding='utf-8',
        level=logging.DEBUG,
        format='{asctime} {name} {levelname:8s} {message}',
        style='{',
        handlers=[rotating_file_handler]
    )