from config.conf import Config
from examples.examplerunner import ExampleRunner

ETH0_BACKEND_NAME = Config.ETH_ENDPOINTS[0]["name"]
ETH0_BACKEND_ADDR = Config.ETH_ENDPOINTS[0]["url"]
ETH1_BACKEND_NAME = Config.ETH_ENDPOINTS[1]["name"]
ETH1_BACKEND_ADDR = Config.ETH_ENDPOINTS[1]["url"]


def example_pass_through_single_device_setup(runner: ExampleRunner):
    runner.start_example_0(name=ETH0_BACKEND_NAME, addr=ETH0_BACKEND_ADDR)


def example_single_endpoint_multiple_priorities_setup(
    runner: ExampleRunner, rate_1: float = 50, rate_2: float = 10
):
    runner.start_example_1(rate_1, rate_2)


def example_method_based_qos_setup(runner: ExampleRunner):
    runner.start_example_2()


def example_interleave_qos_setup(runner: ExampleRunner):
    runner.start_example_3()


def example_load_balancing_qos_setup(runner: ExampleRunner):
    runner.start_example_4()


def example_multi_endpoint_with_infura_priorities_setup(
    runner: ExampleRunner, rate_1: float = 50, rate_2: float = 10
):
    runner.start_example_5(rate_1, rate_2)


def example_multi_endpoint_with_infura_priorities_complex_setup(runner: ExampleRunner):
    runner.start_example_6()


def example_multi_endpoint_with_arch_infura_and_priorities_setup(runner: ExampleRunner):
    runner.start_example_7()


def example_test_load_balancing_multi_device_setup(runner: ExampleRunner):
    # List the available devices to test
    endpoints = [
        (ETH0_BACKEND_ADDR, ETH0_BACKEND_NAME),
        (ETH1_BACKEND_ADDR, ETH1_BACKEND_NAME),
    ]

    runner.start_example_8(endpoints)
