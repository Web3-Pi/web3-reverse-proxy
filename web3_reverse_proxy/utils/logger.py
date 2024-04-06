import logging

from web3_reverse_proxy.config.conf import LOG_LEVEL


logging.basicConfig()
logger = logging.getLogger("Web3ReverseProxy")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))


def get_logger(name: str):
    return logger.getChild(name)
