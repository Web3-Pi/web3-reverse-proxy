import os
import sys

if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.examplerunner import ExampleRunner
from examples.examples import (
    example_load_balancing_qos_setup,
    example_method_based_qos_setup,
    example_multi_endpoint_with_arch_infura_and_priorities_setup,
    example_multi_endpoint_with_infura_priorities_complex_setup,
    example_multi_endpoint_with_infura_priorities_setup,
    example_pass_through_single_device_setup,
    example_single_endpoint_multiple_priorities_setup,
    example_test_load_balancing_multi_device_setup,
)


def example_test():
    runner = ExampleRunner()

    # A few example scenarios to learn from
    example_pass_through_single_device_setup(runner)
    # example_single_endpoint_multiple_priorities_setup(runner, 50, 10)
    # example_method_based_qos_setup(runner)
    # example_load_balancing_qos_setup(runner)
    # example_multi_endpoint_with_infura_priorities_setup(runner, 50, 10)
    # example_multi_endpoint_with_infura_priorities_complex_setup(runner)
    # example_multi_endpoint_with_arch_infura_and_priorities_setup(runner)
    # example_test_load_balancing_multi_device_setup(runner)


if __name__ == "__main__":
    example_test()
