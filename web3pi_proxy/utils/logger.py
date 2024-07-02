import logging

from web3pi_proxy.config.conf import Config

logging.basicConfig()
logger = logging.getLogger("Web3ReverseProxy")
logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))


def get_logger(name: str) -> logging.Logger:
    return logger.getChild(name)
