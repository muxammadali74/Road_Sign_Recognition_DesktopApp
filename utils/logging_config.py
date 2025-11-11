# logging_config.py
import logging
import os
import sys
from datetime import datetime


def setup_logging():
    """Настройка логгирования для приложения"""

    # Создаем папку для логов если её нет
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Имя файла лога с timestamp
    log_filename = f"road_sign_recognition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(log_dir, log_filename)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger("RoadSignRecognition")
    logger.info("=" * 50)
    logger.info("Road Sign Recognition Application Started")
    logger.info("=" * 50)

    return logger


logger = setup_logging()