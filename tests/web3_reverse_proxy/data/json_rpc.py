import random
from typing import Any, Dict, List


VALID_METHOD_PARAMS = {
    "web3_clientVersion": [[], None],
    "web3_sha3": [["0x68656c6c6f20776f726c64"]],
    "net_version": [[], None],
    "net_listening": [[], None],
    "net_peerCount": [[], None],
    "eth_protocolVersion": [[], None],
    "eth_accounts": [[], None],
    "eth_blockNumber": [[], None],
    "eth_call": [
        [
            {
                "from": None,
                "to":"0x6b175474e89094c44da98b954eedeac495271d0f",
                "data":"0x70a082310000000000000000000000006E0d01A76C3Cf4288372a29124A26D4353EE51BE"
            }
        ],
        [
            {
                "from": None,
                "to":"0x6b175474e89094c44da98b954eedeac495271d0f",
                "data":"0x70a082310000000000000000000000006E0d01A76C3Cf4288372a29124A26D4353EE51BE"
            },
            "latest"
        ]
    ],
    "eth_chainId": [[], None],
    "eth_coinbase": [[], None],
    "eth_mining": [[], None],
    "eth_hashrate": [[], None],

    "eth_createAccessList": [
        [
            {
                "from": "0xaeA8F8f781326bfE6A7683C2BD48Dd6AA4d3Ba63",
                "data": "0x608060806080608155"
            }
        ],
        [
            {
                "from": "0xaeA8F8f781326bfE6A7683C2BD48Dd6AA4d3Ba63",
                "data": "0x608060806080608155"
            },
            "pending"
        ]
    ],
    "eth_estimateGas": [
        [
            {
                "from":"0x8D97689C9818892B700e27F316cc3E41e17fBeb9",
                "to":"0xd3CdA913deB6f67967B99D67aCDFa1712C293601",
                "value":"0x186a0"
            }
        ],
        [
            {
                "from":"0x8D97689C9818892B700e27F316cc3E41e17fBeb9",
                "to":"0xd3CdA913deB6f67967B99D67aCDFa1712C293601",
                "value":"0x186a0"
            },
            "latest"
        ]
    ],
    "eth_feeHistory": [[4, "latest", [25, 75]]],
    "eth_gasPrice": [[], None],
    "eth_getBalance": [["0x8D97689C9818892B700e27F316cc3E41e17fBeb9", "latest"]],
    "eth_getBlockByHash": [["0x3f07a9c83155594c000642e7d60e8a8a00038d03e9849171a05ed0e2d47acbb3", False]],
    "eth_getBlockByNumber": [["0xc5043f", False]],
    "eth_getBlockReceipts": [["0xc5043f"]],
    "eth_getBlockTransactionCountByHash": [
        ["0x829df9bb801fc0494abf2f443423a49ffa32964554db71b098d332d87b70a48b"]
    ],
    "eth_getBlockTransactionCountByNumber": [["0xc5043f"]],
    "eth_getCode": [["0x5B56438000bAc5ed2c6E0c1EcFF4354aBfFaf889","latest"]],
    "eth_getFilterChanges": [["0x16"]],
    "eth_getFilterLogs": [["0x16"]],
    "eth_getLogs": [[{"address": "0xdAC17F958D2ee523a2206206994597C13D831ec7"}]],
    "eth_getProof": [
        [
            "0x7F0d15C7FAae65896648C8273B6d7E43f58Fa842",
            ["0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"],
            "latest"
        ]
    ],
    "eth_getStorageAt": [["0xE592427A0AEce92De3Edee1F18E0157C05861564", "0x0", "latest"]],
    "eth_getTransactionByBlockHashAndIndex": [
        ["0x829df9bb801fc0494abf2f443423a49ffa32964554db71b098d332d87b70a48b","0x0"]
    ],
    "eth_getTransactionByBlockNumberAndIndex": [["0xc5043f", "0x0"]],
    "eth_getTransactionByHash": [["0xb1fac2cb5074a4eda8296faebe3b5a3c10b48947dd9a738b2fdf859be0e1fbaf"]],
    "eth_getTransactionCount": [["0x8D97689C9818892B700e27F316cc3E41e17fBeb9", "latest"]],
    "eth_getTransactionReceipt": [["0x85d995eba9763907fdf35cd2034144dd9d53ce32cbec21349d4b12823c6860c5"]],
    "eth_getUncleCountByBlockHash": [["0x829df9bb801fc0494abf2f443423a49ffa32964554db71b098d332d87b70a48b"]],
    "eth_getUncleCountByBlockNumber": [["0xc5043f"]],
    "eth_getUncleByBlockNumberAndIndex": [["0x29c", "0x0"]],
    "eth_getUncleByBlockHashAndIndex": [
        [
            "0xc6ef2fc5426d6ad6fd9e2a26abeab0aa2411b7ab17f30a99d3cb96aed1d1055b",
            "0x0"
        ]
    ],
    "eth_maxPriorityFeePerGas": [[], None],
    "eth_newBlockFilter": [[], None],
    "eth_newFilter": [
        [
            {
                "fromBlock": "0xe20360",
                "toBlock": "0xe20411",
                "address": "0x6b175474e89094c44da98b954eedeac495271d0f",
                "topics": []
            }
        ]
    ],
    "eth_newPendingTransactionFilter": [[], None],
    "eth_sendRawTransaction": [["0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675"]],
    "eth_sendTransaction": [
        [
            {
                "from": "0xb60e8dd61c5d32be8058bb8eb970870f07233155",
                "to": "0xd46e8dd67c5d32be8058bb8eb970870f07244567",
                "gas": "0x76c0",
                "gasPrice": "0x9184e72a000",
                "value": "0x9184e72a",
                "data": "0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675"
            }
        ]
    ],
    "eth_sign": [["0x9b2055d370f73ec7d8a03e965129118dc8f5bf83", "0xdeadbeaf"]],
    "eth_signTransaction": [
        [
            {
                "from": "0xb60e8dd61c5d32be8058bb8eb970870f07233155",
                "to": "0xd46e8dd67c5d32be8058bb8eb970870f07244567",
                "gas": "0x76c0",
                "gasPrice": "0x9184e72a000",
                "value": "0x9184e72a",
                "data": "0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675"
            }
        ]
    ],
    "eth_syncing": [[], None],
    "eth_uninstallFilter": [["0x10ff0bfba9472c87932c56632eef8f5cc70910e8e71d"]],
}

BASE_PAYLOAD = {"jsonrpc": "2.0", "id": 0}


class RPCCalls:
    @classmethod
    def create_json_payload(cls, method: str, params: List[Any]) -> Dict[str, Any]:
        payload = BASE_PAYLOAD.copy()
        payload["method"] = method
        if params is not None:
            payload["params"] = params
        return payload

    @classmethod
    def create_json_payload_without_member(cls, method: str, params: List[Any], member: str) -> Dict[str, Any]:
        payload = cls.create_json_payload(method, params)
        del(payload[member])
        return payload

    @classmethod
    def generate_valid_calls(cls) -> List[Dict[str, Any]]:
        valid_calls = []
        for method, params_set in VALID_METHOD_PARAMS.items():
            for params in params_set:
                valid_calls.append(cls.create_json_payload(method, params))
        return valid_calls

    @classmethod
    def generate_missing_member_calls(cls) -> List[Dict[str, Any]]:
        missing_member_calls = []
        for member in ["jsonrpc", "method", "id"]:
            methods = list(VALID_METHOD_PARAMS.keys())
            for method in methods:
                for params in VALID_METHOD_PARAMS[method]:
                    payload = cls.create_json_payload_without_member(method, params, member)
                    missing_member_calls.append(payload)
        return missing_member_calls

    @classmethod
    def generate_non_alphanumeric_input_calls(cls) -> List[Dict[str, Any]]:
        non_alphanumeric_set = "`~!@#$%^&*()-=+[]{};:'\",.<>/?"

        non_alphanumeric_input_calls = []
        methods = list(VALID_METHOD_PARAMS.keys())
        for method in methods:
            for params in VALID_METHOD_PARAMS[method]:
                if params is not None and len(params) > 0:
                    non_alnum_index = methods.index(method) % (len(non_alphanumeric_set) - 1)
                    new_params = params[:-1] + [non_alphanumeric_set[non_alnum_index]]
                    payload = cls.create_json_payload(method, new_params)
                    non_alphanumeric_input_calls += [payload]
        return non_alphanumeric_input_calls

    @classmethod
    def generate_stress_test_calls(cls, method="eth_sendTransaction", count=1000) -> List[Dict[str, Any]]:
       return [cls.create_json_payload(method, VALID_METHOD_PARAMS[method][-1])] * count