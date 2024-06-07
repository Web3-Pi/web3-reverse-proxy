# Web3Pi Reverse Proxy

A reverse proxy for Geth intended for use within Web3Pi ecosystem.

Web3Pi Reverse Proxy comes out-of-the-box with several features:
 
 - Multiple geth nodes - you can hide multiple Geth nodes under single instance of reverse proxy
 - JSON-RPC parser - our custom parser validates JSON-RPC requests before they reach the nodes
 - Admin portal - comes embedded in, allowing you the following:
	- Authentication - generate API-keys and control access to your reverse proxy
	- User plans - control how much data users can process
	- Activity stats - see how much data each user processes, monitor node usage
 
## Setup

Simply install `web3pi-reverse-proxy` package using your Python package manager, using **pip** for example:

```bash
pip install web3pi-reverse-proxy
```

Web3Pi Reverse Proxy expects you to provide **ETH_ENDPOINTS** environment variable to your system.

It should be a list of endpoint descriptors for JSON-RPC over HTTP communication with Geth.

Refer to the following example:

```bash
export ETH_ENDPOINTS='[{"name": "rpi geth 1", "url": "http://eop-1.local:8545/"}, {"name": "infura", "url": "https://mainnet.infura.io/v3/<YOUR_INFURA_API_KEY>"}]'
```

You can define as many endpoints as you wish and chose their names however suits you.

## Run

After configuring endpoints, you can run your reverse proxy with command

```bash
rproxy-run
```

Admin panel starts alongside the reverse proxy, you can access it by appending your **HTTP_SERVER_ADMIN_ACCESS_TOKEN** to your reverse proxy's URL, like so:

```
http://0.0.0.0:6561/<HTTP_SERVER_ADMIN_ACCESS_TOKEN>
```

The **HTTP_SERVER_ADMIN_ACCESS_TOKEN** is will be output to your terminal, during the launch.

