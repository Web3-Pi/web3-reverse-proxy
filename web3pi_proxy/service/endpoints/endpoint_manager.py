import json
from typing import Optional, Union

from dotenv import dotenv_values, find_dotenv, set_key
from peewee import PeeweeException

from web3pi_proxy.config import Config
from web3pi_proxy.core.rpc.node.endpoint_pool.pool_manager import (
    EndpointConnectionPoolManager,
    EndpointConnectionPool,
    PoolAlreadyExistsError,
    PoolDoesNotExistError,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3pi_proxy.db.models import Endpoint


class EndpointManagerService:
    def __init__(self, endpoint_pool_manager: EndpointConnectionPoolManager) -> None:
        self.endpoint_pool_manager = endpoint_pool_manager

    def __write_conf_to_file(self, config: dict) -> None:
        env_file = find_dotenv()

        for key, value in config.items():
            set_key(dotenv_path=env_file, key_to_set=key, value_to_set=value)

    def __save_endpoint_conf(self, name: str, url: Optional[str]):
        env = dotenv_values(".env")
        endpoints_config = json.loads(env["ETH_ENDPOINTS"])

        index = 0
        while index < len(endpoints_config) and endpoints_config[index]["name"] != name:
            index += 1
        if index < len(endpoints_config):
            if not url:
                del endpoints_config[index]
            else:
                endpoints_config[index]["url"] = url
        elif url:
            endpoints_config.append({"name": name, "url": url})

        self.__write_conf_to_file({"ETH_ENDPOINTS": json.dumps(endpoints_config)})

    def get_pool(self, name: str) -> EndpointConnectionPool:
        return self.endpoint_pool_manager.get_pool(name)

    def get_endpoints(self) -> dict:
        nodes_data = {}
        for endpoint in self.endpoint_pool_manager.endpoints:
            endpoint_entry = {}
            endpoint_entry["host"] = endpoint.conn_descr.host
            endpoint_entry["port"] = endpoint.conn_descr.port
            endpoint_entry["auth_key"] = endpoint.conn_descr.auth_key
            endpoint_entry["is_ssl"] = endpoint.conn_descr.is_ssl
            endpoint_entry["url"] = endpoint.conn_descr.url
            nodes_data[endpoint.get_name()] = endpoint_entry
        return nodes_data

    def add_endpoint(self, name: str, url: str) -> Union[RPCEndpoint, dict]:
        if not Config.ETH_ENDPOINTS_STORE:
            return {"error": "the endpoint cannot be stored"}
        descriptor = EndpointConnectionDescriptor.from_url(url)
        if descriptor is None:
            return {"error": "Invalid URL provided"}
        try:
            endpoint = self.endpoint_pool_manager.add_pool(name, descriptor)
        except PoolAlreadyExistsError as error:
            return {"error": error.message}
        config = json.dumps({"name": name, "url": url})
        try:
            Endpoint.create(name=name, config=config)
        except PeeweeException as error:
            self.endpoint_pool_manager.remove_pool(name)  # TODO use db tx instead?
            return {"error": str(error)}
        return endpoint

    def remove_endpoint(self, name: str) -> Union[RPCEndpoint, dict]:
        if not Config.ETH_ENDPOINTS_STORE:
            return {"error": "the endpoint cannot be stored"}
        try:
            endpoint = self.endpoint_pool_manager.remove_pool(name)
        except PoolDoesNotExistError as error:
            return {"error": error.message}
        try:
            Endpoint.delete().where(Endpoint.name == name).execute()
        except PeeweeException as error:
            return {"error": "(db inconsistent): " + str(error)}  # TODO handle inconsistency
        return endpoint

    def update_endpoint(self, name: str, url: str) -> Union[RPCEndpoint, dict]:
        if not Config.ETH_ENDPOINTS_STORE:
            return {"error": "the endpoint cannot be stored"}
        descriptor = EndpointConnectionDescriptor.from_url(url)
        if descriptor is None:
            return {"error": "Invalid URL provided"}
        try:
            self.endpoint_pool_manager.remove_pool(name)
        except PoolDoesNotExistError as error:
            return {"error": error.message}
        endpoint = self.endpoint_pool_manager.add_pool(name, descriptor)
        try:
            endpoint_db = Endpoint.get(Endpoint.name == name)
            config = json.dumps({"name": name, "url": url})
            endpoint_db.config = config
            endpoint_db.save()
        except PeeweeException as error:
            return {"error": "(db inconsistent): " + str(error)}  # TODO handle inconsistency
        return endpoint
