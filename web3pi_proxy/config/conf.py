import json
import os
from typing import List, Union, get_type_hints
from enum import Enum

from dotenv import dotenv_values


class ProxyMode(Enum):
    DEV = "DEV"
    SIM = "SIM"
    PROD = "PROD"


def _parse_bool(val: Union[str, bool]) -> bool:
    return val if val is bool else val.lower() in ["true", "yes", "1"]


class AppConfig:
    LOG_LEVEL: str = "INFO"

    # global socket conf
    DEFAULT_RECV_BUF_SIZE: int = 8192

    # default rpc service conf
    PUBLIC_SERVICE: bool = False

    # UPnP
    USE_UPNP: bool = True and PUBLIC_SERVICE
    UPNP_DISCOVERY_TIMEOUT: float = 2.5
    UPNP_LEASE_TIME: int = 5 * 3600

    # server socket conf
    PROXY_LISTEN_ADDRESS: str = "0.0.0.0"
    PROXY_LISTEN_PORT: int = 6512
    NUM_PROXY_WORKERS: int = 150
    MAX_PENDING_CLIENT_SOCKETS: int = 10_000
    MAX_CONCURRENT_CONNECTIONS: int = 21
    MAX_SATURATED_ITERATIONS_LISTEN_PARAM: int = 2
    # unused conn to eth rpc node is closed between IDLE_CONNECTION_TIMEOUT and 2*IDLE_CONNECTION_TIMEOUT, seconds
    IDLE_CONNECTION_TIMEOUT: int = 300
    SSL_ENABLED: bool = False
    SSL_CERT_FILE: str = "cert.pem"
    SSL_KEY_FILE: str = "key.pem"

    LISTEN_BACKLOG_PARAM: int = 21
    BLOCKING_ACCEPT_TIMEOUT: int = 5

    QOS_BASE_FREQUENCY: int = 200

    # Endpoints
    ETH_ENDPOINTS: List[dict] = [
        {"name": "eop-1", "url": "http://eop-1.local:8545/"},
        # {"name": "rpi4 geth2", "url": "http://geth-2.local:8545/"},
        # {"name": "infura-1", "url": "https://mainnet.infura.io/v3/<YOUR_INFURA_KEY>"}
    ]

    CACHE_ENABLED: bool = False
    CACHE_EXPIRY_MS: int = 300000

    # parser
    JSON_RPC_REQUEST_PARSER_ENABLED: bool = True

    # rudimentary stats update conf
    STATS_UPDATE_DELTA: int = 12
    STATS_UPDATE_MIN_DELAY: float = 0.1

    # administration
    ADMIN_LISTEN_PORT: int = 6561
    # empty value means to generate a new random
    ADMIN_AUTH_TOKEN: str = ""

    # default pickle database to store stats
    DB_FILE: str = "web3pi_proxy.sqlite3"
    STATE_STORAGE_FILE: str = f"{os.getcwd()}/.w3appdata/{DB_FILE}"

    # admin panel
    ADMIN_ROOT_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    ADMIN_HTML_FILE: str = f"{ADMIN_ROOT_DIR}/admin/admin/admin.html"

    # console info
    SERVICE_NAME: str = "Web3 RPC Reverse Proxy Service"
    SERVICE_VER: str = "0.0.2"

    PROXY_NAME: str = "Web3 RPC Reverse Proxy"
    PROXY_VER: str = "0.0.2"

    # convenience setting - default users creation if DEV
    MODE: ProxyMode = ProxyMode.PROD

    LOADBALANCER: str = "LeastBusyLoadBalancer"

    def __init__(self):
        env = {
            **dotenv_values(".env"),  # load shared development variables
            **os.environ,  # override loaded values with environment variables
        }

        for field in self.__annotations__:
            if not field.isupper():
                continue

            env_value = env.get(field)
            if not env_value:
                continue

            # Cast env var value to expected type
            if field == "ETH_ENDPOINTS":
                value = json.loads(env_value)
            elif field == "MODE":
                try:
                    value = ProxyMode(env_value.upper())
                except ValueError:
                    print("Unrecognized MODE", env_value, "available modes: DEV, SIM, PROD")
                    raise Exception("Unrecognized MODE")
            elif field == "LOADBALANCER":
                if env_value in ["RandomLoadBalancer", "LeastBusyLoadBalancer", "ConstantLoadBalancer"]:
                    value = env_value
                else:
                    print("Unrecognized LOADBALANCER, switching to the default")
                    value = "LeastBusyLoadBalancer"
            else:
                var_type = get_type_hints(AppConfig)[field]
                if var_type == bool:
                    value = _parse_bool(env_value)
                else:
                    value = var_type(env_value)

            self.__setattr__(field, value)


Config = AppConfig()
