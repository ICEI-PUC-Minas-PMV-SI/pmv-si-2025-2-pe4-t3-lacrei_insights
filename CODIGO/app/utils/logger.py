import logging
import sys
import os
from datetime import datetime

def get_logger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Cria diretório de logs (se não existir)
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Nome do arquivo de log com data atual
    log_filename = f"etl_{datetime.now().strftime('%Y-%m-%d')}.log"
    log_path = os.path.join(log_dir, log_filename)

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Evita adicionar múltiplos handlers em execuções subsequentes
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
