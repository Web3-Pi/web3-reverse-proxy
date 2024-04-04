import os
from typing import get_type_hints, Union, List
from dotenv import dotenv_values
import json

def _parse_bool(val: Union[str, bool]) -> bool:
    return val if val is bool else val.lower() in ['true', 'yes', '1']


class AppConfig:
    # global socket conf
    DEFAULT_RECV_BUF_SIZE: int = 8192

    # default rpc service conf
    PUBLIC_SERVICE: bool = False
    USE_PICKLE_DB: bool = True

    # UPnP
    USE_UPNP: bool = True and PUBLIC_SERVICE
    UPNP_DISCOVERY_TIMEOUT: float = 2.5
    UPNP_LEASE_TIME: int = 5 * 3600

    # server socket conf
    PROXY_LISTEN_ADDRESS: str = "0.0.0.0"
    PROXY_LISTEN_PORT: int = 6512
    MAX_CONCURRENT_CONNECTIONS: int = 21
    MAX_SATURATED_ITERATIONS_LISTEN_PARAM: int = 2

    LISTEN_BACKLOG_PARAM: int = 21
    BLOCKING_ACCEPT_TIMEOUT: int = 5

    QOS_BASE_FREQUENCY: int = 200

    # Endpoints
    ETH_ENDPOINTS: List[dict] = [
        {"name": "rpi4 geth1", "url": "http://geth-1.local:8545/"},
        # {"name": "rpi4 geth2", "url": "http://geth-2.local:8545/"},
        # {"name": "infura-1", "url": "https://mainnet.infura.io/v3/<YOUR_INFURA_KEY>"}
    ]

    CACHE_ENABLED: bool = True
    CACHE_EXPIRY_MS: int = 300000

    # rudimentary stats update conf
    STATS_UPDATE_DELTA: int = 12
    STATS_UPDATE_MIN_DELAY: float = 0.1

    # administration
    ADMIN_LISTEN_PORT: int = 6561

    # default pickle database to store stats
    DB_FILE: str = "basic_state_db.pickle"
    STATE_STORAGE_FILE: str = f"{os.getcwd()}/.w3appdata/{DB_FILE}"

    # admin panel
    ADMIN_ROOT_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ADMIN_HTML_FILE: str = f'{ADMIN_ROOT_DIR}/web3-reverse-proxy-admin/admin/admin.html'

    # console info
    SERVICE_NAME: str = "Web3 RPC Reverse Proxy Service  - RPI4 Edition"
    SERVICE_VER: str = "0.0.1"

    PROXY_NAME: str = "Web3 RPC Reverse Proxy - RPI4 Edition"
    PROXY_VER: str = "0.0.1"

    # convenience flag - default users creation
    FORCE_REGISTER_DEFAULT_USERS: bool = True

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
            else:
                var_type = get_type_hints(AppConfig)[field]
                if var_type == bool:
                    value = _parse_bool(env_value)
                else:
                    value = var_type(env_value)

            self.__setattr__(field, value)


Config = AppConfig()
