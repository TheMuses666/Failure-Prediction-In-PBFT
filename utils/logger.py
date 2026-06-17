import logging

def get_logger(name):
    # 1. create logger
    logger = logging.getLogger(name)

    # 2. create level
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # 3. create handler
        handler = logging.StreamHandler()

        # 4. create format
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

        # 5. assembly
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

