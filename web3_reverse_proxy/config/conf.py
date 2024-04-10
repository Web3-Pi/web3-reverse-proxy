import os

# global socket conf
DEFAULT_RECV_BUF_SIZE = 8192

# default rpc service conf
PUBLIC_SERVICE = False
USE_PICKLE_DB = True

# UPnP
USE_UPNP = True and PUBLIC_SERVICE
UPNP_DISCOVERY_TIMEOUT = 2.5
UPNP_LEASE_TIME = 5 * 3600

# server socket conf
PROXY_LISTEN_ADDRESS = "0.0.0.0"
PROXY_LISTEN_PORT = 6512
MAX_CONCURRENT_CONNECTIONS = 21
MAX_SATURATED_ITERATIONS_LISTEN_PARAM = 2
SSL_ENABLED = False
SSL_CERT_FILE = "cert.pem"
SSL_KEY_FILE = "key.pem"

LISTEN_BACKLOG_PARAM = 21
BLOCKING_ACCEPT_TIMEOUT = 5

QOS_BASE_FREQUENCY = 200

# Endpoints
ETH_ENDPOINTS = [
    ("rpi4 geth1", "http://geth-1.local:8545/"),
    # ("rpi4 geth2", "http://geth-2.local:8545/"),
    # ("infura-1", "https://mainnet.infura.io/v3/<YOUR_INFURA_KEY>")
]

CACHE_ENABLED = False
CACHE_EXPIRY_MS = 300000

# parser
JSON_RPC_REQUEST_PARSER_ENABLED = True

# rudimentary stats update conf
STATS_UPDATE_DELTA = 12
STATS_UPDATE_MIN_DELAY = 0.1

# administration
ADMIN_LISTEN_PORT = 6561

# default pickle database to store stats
DB_FILE = "basic_state_db.pickle"
STATE_STORAGE_FILE = f"{os.getcwd()}/.w3appdata/{DB_FILE}"

# admin panel
ADMIN_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADMIN_HTML_FILE = f'{ADMIN_ROOT_DIR}/web3-reverse-proxy-admin/admin/admin.html'

# console info
SERVICE_NAME = "Web3 RPC Reverse Proxy Service  - RPI4 Edition"
SERVICE_VER = "0.0.1"

PROXY_NAME = "Web3 RPC Reverse Proxy - RPI4 Edition"
PROXY_VER = "0.0.1"

# convenience flag - default users creation
FORCE_REGISTER_DEFAULT_USERS = True
