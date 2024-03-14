# A test with subgraph for Web3-Pi reverse proxy

## Install and Deploy

Prerequisites:

1. `npm` version `>=18`.
2. Up and running subgraph node. If it is not locally, please update the addresses in `package.json`. See Configure and Run the node.

Instruction:

1. `npm ci`.
2. `npm run codegen`
3. `npm run create`
4. `npm run deploy`

## Configure and Run the node

1. `cp .env.example .env`.
2. Edit and configure `.env`.
3. `docker-compose up` or `docker-compose up -d`.

