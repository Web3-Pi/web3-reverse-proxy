"""
TODO: Parsing tests are covered by unit tests, but valid calls could still be made into an E2E test.
Consider refactoring this for compatibility with a test runner.
"""
import requests
import time
import pytest

from web3_reverse_proxy.tests.data.json_rpc import RPCCalls
from web3_reverse_proxy.utils.logger import get_logger


logger = get_logger("ParserE2ETest")
pytest.skip("skipping incompatible E2E", allow_module_level=True)


URL = 'http://localhost:6512/aaa'


def make_request(payload):
    logger.info(f"Sending command: {payload}")
    return requests.post(URL, json=payload, headers={'Content-Type': 'application/json'})


def send_valid_requests():
    print("Sending valid requests...")
    failed_requests = []
    total_requests = 0
    timestamp = time.time()
    for payload in RPCCalls.generate_valid_calls():
        response = make_request(payload)
        total_requests += 1
        if not response.ok:
            failed_requests.append((payload["method"], payload.get("params")))
            logger.error(f"Responded with error: {response._content}\n")
        else:
            logger.info(f"Received response: {response}")
            logger.info(f"With content: {response._content}\n")
    runtime = time.time() - timestamp
    print(f"Finished in {runtime}")
    print(f'Failed {len(failed_requests)} out of {total_requests} requests\n')
    if len(failed_requests) > 0:
        print(f'Failed following requests:\n')
        for method, params in failed_requests:
            print(f"{method} -> {params}")
    print("\n")


def send_missing_member_calls():
    print("Sending requests with missing members in JSON-RPC object...")
    passed_requests = []
    total_requests = 0
    timestamp = time.time()
    for payload in RPCCalls.generate_missing_member_calls():
        response = make_request(payload)
        total_requests += 1
        if not response.ok:
            logger.info(f"Responded with error: {response._content}\n")
        else:
            passed_requests.append((payload.get('method'), payload.get('params')))
            logger.error(f"Request passed with response: {response}")
            logger.error(f"With content: {response._content}\n")
    runtime = time.time() - timestamp
    print(f"Finished in {runtime}")
    print(f'Passed {len(passed_requests)} out of {total_requests} requests\n')
    if len(passed_requests) > 0:
        print(f'Passed following requests:\n')
        for method, params in passed_requests:
            print(f"{method} -> {params}")
    print("\n")


def send_non_alphanumeric_input_calls():
    print("Sending requests with non-alphanumeric content in JSON-RPC object...")
    passed_requests = []
    total_requests = 0
    timestamp = time.time()
    for payload in RPCCalls.generate_non_alphanumeric_input_calls():
        response = make_request(payload)
        total_requests += 1
        if not response.ok:
            logger.info(f"Responded with error: {response._content}\n")
        else:
            passed_requests.append((payload['method'], payload.get(('params'))))
            logger.error(f"Request passed with response: {response}")
            logger.error(f"With content: {response._content}\n")
    runtime = time.time() - timestamp
    print(f"Finished in {runtime}")
    print(f'Passed {len(passed_requests)} out of {total_requests} requests\n')
    if len(passed_requests) > 0:
        print(f'Passed following requests:\n')
        for method, params in passed_requests:
            print(f"{method} -> {params}")
    print("\n")


def stress_test(method="eth_sendTransaction", count=1000):
    print(f"Sending {count} x {method} calls")
    timestamp = time.time()
    calls = RPCCalls.generate_stress_test_calls(method, count)
    for i in range(len(calls)):
        logger.info(f"Sending {i + 1} out of {count} calls")
        make_request(calls[i])
    runtime = time.time() - timestamp
    print(f"Finished in {runtime}")


def main():
    send_valid_requests()
    send_missing_member_calls()
    send_non_alphanumeric_input_calls()
    # stress_test()


if __name__ == '__main__':
    main()
