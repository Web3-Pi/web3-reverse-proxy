# RPC Reverse Proxy

A reverse proxy for Geth intended for use within Web3Pi ecosystem.

RPC Reverse Proxy comes out-of-the-box with several features:
 
 - Multiple geth nodes - you can hide multiple Geth nodes under single instance of reverse proxy
 - JSON-RPC parser - our custom parser validates JSON-RPC requests before they reach the nodes
 - Admin portal - comes embedded in, allowing you the following:
	- Authentication - generate API-keys and control access to your reverse proxy
	- User plans - control how much data users can process
	- Activity stats - see how much data each user processes, monitor node usage
	- Admin API - use JSON-RPC based API to perform various operations on your reverse proxy
 
## Setup

You can install `web3pi-proxy` in one of two ways:

### Install via PyPI

Simply install `web3pi-proxy` package using your Python package manager, using **pip** for example:

```bash
pip install web3pi-proxy
```

### Install from source

To install the package from source, follow these steps:

```bash
git clone https://github.com/Web3-Pi/web3-reverse-proxy.git
cd web3-reverse-proxy
python3 -m venv venv
source venv/bin/activate
pip install poetry
poetry install
```

## Configuration

You can define the following environment variables, and you can place them in the .env file (all are optional):

| Variable                        | Description                                                                                                                                                 | Default                                |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `LOG_LEVEL`                     | Specifies the logging level.                                                                                                                               | `INFO`                                 |
| `ADMIN_AUTH_TOKEN`              | Admin authentication token.                  | Randomly generated                    |
| `ETH_ENDPOINTS`                 | A JSON list of endpoint descriptors for Ethereum nodes. Example: `[{"name": "rpi4", "url": "http://localhost:8545/"}]`. If defined, this list becomes static and cannot be managed via the admin panel. Leaving it undefined enables endpoint management via a local database. | `None`                                |
| `DEFAULT_RECV_BUF_SIZE`         | Buffer size for socket receiving.                                                                                                                          | `8192`                                |
| `PUBLIC_SERVICE`                | Whether the service is public.                                                                                                                             | `False`                               |
| `USE_UPNP`                      | Enables UPnP if `PUBLIC_SERVICE` is `True`.                                                                                                                | `True`                                |
| `UPNP_DISCOVERY_TIMEOUT`        | Timeout for UPnP discovery in seconds.                                                                                                                     | `2.5`                                 |
| `UPNP_LEASE_TIME`               | Lease time for UPnP in seconds.                                                                                                                            | `18000` (5 hours)                     |
| `PROXY_LISTEN_ADDRESS`          | Address for the proxy to listen on.                                                                                                                        | `0.0.0.0`                             |
| `PROXY_CONNECTION_ADDRESS`      | Address clients use to connect to the proxy. Default is `None` (auto-resolved).                                                                             | `None`                                |
| `PROXY_LISTEN_PORT`             | Port for the proxy to listen on.                                                                                                                            | `6512`                                |
| `NUM_PROXY_WORKERS`             | Number of workers handling proxy connections.                                                                                                              | `150`                                 |
| `MAX_PENDING_CLIENT_SOCKETS`    | Maximum number of pending client sockets.                                                                                                                  | `10000`                               |
| `MAX_CONCURRENT_CONNECTIONS`    | Maximum number of concurrent connections.                                                                                                                  | `21`                                  |
| `IDLE_CONNECTION_TIMEOUT`       | Timeout for idle connections in seconds.                                                                                                                   | `300`                                 |
| `SSL_ENABLED`                   | Whether SSL is enabled.                                                                                                                                    | `False`                               |
| `SSL_CERT_FILE`                 | Path to SSL certificate file.                                                                                                                              | `cert.pem`                            |
| `SSL_KEY_FILE`                  | Path to SSL key file.                                                                                                                                      | `key.pem`                             |
| `CACHE_ENABLED`                 | Whether caching is enabled.                                                                                                                                | `False`                               |
| `CACHE_EXPIRY_MS`               | Cache expiry time in milliseconds.                                                                                                                         | `300000` (5 minutes)                  |
| `JSON_RPC_REQUEST_PARSER_ENABLED` | Enables JSON-RPC request parsing.                                                                                                                          | `True`                                |
| `STATS_UPDATE_DELTA`            | Update interval for stats in seconds.                                                                                                                      | `12`                                  |
| `ADMIN_LISTEN_ADDRESS`          | Address for the admin panel to listen on.                                                                                                                  | `0.0.0.0`                             |
| `ADMIN_CONNECTION_ADDRESS`      | Address clients use to connect to the admin panel. Default is `None` (auto-resolved).                                                                       | `None`                                |
| `ADMIN_LISTEN_PORT`             | Port for the admin panel to listen on.                                                                                                                     | `6561`                                |
| `DB_FILE`                       | Path to the database file.                                                                                                                                 | `web3pi_proxy.sqlite3`                |
| `MODE`                          | Proxy mode (`DEV`, `SIM`, `PROD`).                                                                                                                          | `PROD`                                |
| `LOADBALANCER`                  | Load balancer strategy (`RandomLoadBalancer`, `LeastBusyLoadBalancer`, `ConstantLoadBalancer`).                                                             | `LeastBusyLoadBalancer`               |


## Run

You can run your reverse proxy with command:

```bash
web3pi-proxy
```

## Admin service

Admin service starts alongside the reverse proxy.


You can access admin webpage with your browser using admin server's URL and providing **admin auth token** as a 'token' query param, like so:

```
http://0.0.0.0:6561/?token=<ADMIN_AUTH_TOKEN>
```

### Reference Image

![Admin Panel](./admin/docs/screenshot_admin_example.jpg)


The **admin auth token** will be output to your terminal, during the launch.

Token is not stored and will be randomly generated on each launch, unless it has been defined as an environment variable or in the .env file.

Outside of admin portal, the admin service allows several operations, performed by submitting JSON-RPC requests.
Use **admin auth token** in **Authorization** header of your HTTP POST request for authentication.

### get_endpoints
Get list of currently configured endpoints, no parameters required.

### add_endpoint
Add new endpoint at runtime by providing its **name** and **URL**. For example, in order to add endpoint ***local*** under URL ***localhost:8545*** :

```
{"jsonrpc": "2.0", "method": "add_endpoint", "params": ["local", "http://localhost:8545/"], "id": 0}
```

**IMPORTANT:** Resulting changes are saved in local `.env` file for reuse.

### update_endpoint
Change existing endpoint's configuration at runtime by providing its **name** and **URL**. For example, in order to change endpoint's ***local*** port to ***8546*** :

```
{"jsonrpc": "2.0", "method": "update_endpoint", "params": ["local", "http://localhost:8546/"], "id": 0}
```

**IMPORTANT:** Resulting changes are saved in local `.env` file for reuse.

### remove_endpoint
Remove endpoint at runtime by providing its **name**. For example, in order to remove endpoint ***local*** :

```
{"jsonrpc": "2.0", "method": "remove_endpoint", "params": ["local"], "id": 0}
```

**IMPORTANT:** Resulting changes are saved in local `.env` file for reuse.

## Wallet integration

Any client can connet RPC Reverse Proxy. 
A web client, scripting tools, backend servers etc. 
It is the same as with other Ethereum RPC providers: you need to use a user's access URL containing API key.
The proxy supports CORS, which enables usage within web browsers.

Users may wish to integrate the proxy with wallet applications, e.g. Metamask.
Below is the example of a proper configuration.
It is convenient to create a duplicate of Mainnet network configuration.
The only specific piece of setup is the RPC URL, which needs to be set to the access URL (that contains proxy's RPC endpoint and user's API key).
See the example below.

![Metamask](./admin/docs/metamask-1.png)

In case of any problems with the verification of the newly added network, the best place to start the investigation is to check the network traffic,
for instance with the web browser's dev tools/developers tools (Ctrl+Shift+C).

