import logging
from . import constants


class NukeHandler(logging.Handler):
    def emit(self, record):
        try:
            print(self.format(record))
        except Exception:
            pass


def getLogger(module_name):
    logger = logging.getLogger(module_name)
    logger.setLevel(constants.logging_level)
    logger.propagate = False

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s:SgVR:%(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    ch = logging.StreamHandler()
    ch.setLevel(constants.logging_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    nh = NukeHandler()
    nh.setLevel(constants.logging_level)
    nh.setFormatter(formatter)
    logger.addHandler(nh)

    return logger
