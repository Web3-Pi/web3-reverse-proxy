from abc import ABC
from typing import Any

from web3pi_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.validation.conditions import (
    Exact,
    In,
    Matches,
    Type,
)
from web3pi_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.validation.errors import (
    InvalidParamsError,
    InvalidRequestError,
    MethodNotFoundError,
)


class JSONValidator(ABC):
    @classmethod
    def validate(cls, content: dict) -> None:
        pass


class JSONRPCFormatValidator(JSONValidator):
    RPC_PARAM_CONDITIONS = {
        "method": Type(Exact(str)),
        "id": Type(In(int, str, type(None))),
        "params": Type(Exact(list)),
        "jsonrpc": Exact("2.0"),
    }

    @classmethod
    def validate(cls, content: dict) -> None:
        if type(content) != dict:
            raise InvalidRequestError(
                f"JSON-RPC request must be an object, batches are not supported"
            )
        for key, condition in cls.RPC_PARAM_CONDITIONS.items():
            if not key in content:
                if key != "params":
                    raise InvalidRequestError(f"Missing member '{key}'")
            elif not condition.validate(content[key]):
                raise InvalidRequestError(f"Invalid value for member '{key}'")


class JSONRPCContentValidator(JSONValidator):
    REGEX_CONDITION = Matches(r"^\w+$")

    def get_error_message(label, value):
        value = value.replace('"', '\\"')
        return f"Invalid characters at {label} '{value}' in params"

    @classmethod
    def traverse_and_validate_params(cls, param_value: Any) -> None:
        if type(param_value) is dict:
            for key in param_value.keys():
                if not cls.REGEX_CONDITION.validate(key):
                    error_message = cls.get_error_message("key", key)
                    raise InvalidParamsError(error_message)
            for sub_param_value in param_value.values():
                cls.traverse_and_validate_params(sub_param_value)
        elif type(param_value) is list:
            for sub_param_value in param_value:
                cls.traverse_and_validate_params(sub_param_value)
        else:
            if not cls.REGEX_CONDITION.validate(param_value):
                error_message = cls.get_error_message("label", param_value)
                raise InvalidParamsError(error_message)

    @classmethod
    def validate(cls, content: dict) -> None:
        cls.traverse_and_validate_params(content.get("params", []))


class JSONRPCMethodValidator(JSONValidator):
    METHOD_PARAM_COUNT_CONDITIONS = {
        "net_peerCount": Exact(0),
        "net_listening": Exact(0),
        "net_version": Exact(0),
        "web3_clientVersion": Exact(0),
        "web3_sha3": Exact(1),
        "eth_protocolVersion": Exact(0),
        "eth_accounts": Exact(0),
        "eth_blockNumber": Exact(0),
        "eth_call": In(1, 2),
        "eth_chainId": Exact(0),
        "eth_coinbase": Exact(0),
        "eth_mining": Exact(0),
        "eth_hashrate": Exact(0),
        "eth_createAccessList": In(1, 2),
        "eth_estimateGas": In(1, 2),
        "eth_feeHistory": Exact(3),
        "eth_gasPrice": Exact(0),
        "eth_getBalance": Exact(2),
        "eth_getBlockByHash": Exact(2),
        "eth_getBlockByNumber": Exact(2),
        "eth_getBlockReceipts": Exact(1),
        "eth_getBlockTransactionCountByHash": Exact(1),
        "eth_getBlockTransactionCountByNumber": Exact(1),
        "eth_getCode": Exact(2),
        "eth_getFilterChanges": Exact(1),
        "eth_getFilterLogs": Exact(1),
        "eth_getLogs": Exact(1),
        "eth_getProof": Exact(3),
        "eth_getStorageAt": Exact(3),
        "eth_getTransactionByBlockHashAndIndex": Exact(2),
        "eth_getTransactionByBlockNumberAndIndex": Exact(2),
        "eth_getTransactionByHash": Exact(1),
        "eth_getTransactionCount": Exact(2),
        "eth_getTransactionReceipt": Exact(1),
        "eth_getUncleCountByBlockHash": Exact(1),
        "eth_getUncleCountByBlockNumber": Exact(1),
        "eth_getUncleByBlockNumberAndIndex": Exact(2),
        "eth_getUncleByBlockHashAndIndex": Exact(2),
        "eth_maxPriorityFeePerGas": Exact(0),
        "eth_newBlockFilter": Exact(0),
        "eth_newFilter": Exact(1),
        "eth_newPendingTransactionFilter": Exact(0),
        "eth_sendRawTransaction": Exact(1),
        "eth_sendTransaction": Exact(1),
        "eth_sign": Exact(2),
        "eth_signTransaction": Exact(1),
        "eth_syncing": Exact(0),
        "eth_uninstallFilter": Exact(1),
    }

    @classmethod
    def validate(cls, content: dict) -> None:
        method_name = content.get("method")
        method_params = content.get("params", [])
        params_length = len(method_params)

        method_condition = cls.METHOD_PARAM_COUNT_CONDITIONS.get(method_name)
        if method_condition is None:
            raise MethodNotFoundError(f"Unsupported method '{method_name}'")
        if not method_condition.validate(params_length):
            raise InvalidParamsError(
                f"Number of parameters for method '{method_name}' {method_condition.description}, "
                f"but {params_length} were given"
            )
