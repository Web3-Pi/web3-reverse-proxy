from contextlib import redirect_stdout
from typing import Callable, List, Tuple

from web3_reverse_proxy.config.conf import Config

from web3_reverse_proxy.service.factories.endpointshandlermiddlewarefactory import RPCEndpointsHandlerMiddlewareFactory

from web3_reverse_proxy.examples.runnerservice.endpointsfactory import ExampleHandlerMiddlewareFactory
from web3_reverse_proxy.examples.runnerservice.examplerunnerservice import ExampleRunnerService
from web3_reverse_proxy.service.ioredirect.stdoutcapture import StdOutCaptureStreamTee


ETH0_BACKEND_NAME = Config.ETH_ENDPOINTS[0]["name"]
ETH0_BACKEND_ADDR = Config.ETH_ENDPOINTS[0]["url"]
INFURA_NAME = Config.ETH_ENDPOINTS[2]["name"]
INFURA_ADDR = Config.ETH_ENDPOINTS[2]["url"]


class ExampleRunner:

    def __init__(self):
        self.new_stdout = StdOutCaptureStreamTee()

        with redirect_stdout(self.new_stdout):
            self.runner_service = ExampleRunnerService(self.new_stdout)
            self.ssm = self.runner_service.get_state_manager()
            self.updater = self.ssm.get_service_state_updater_instance()

    @staticmethod
    def capture_stdout(func: Callable):
        def inner(self, *args, **kwargs):
            with redirect_stdout(self.new_stdout):
                func(self, *args, **kwargs)

        return inner

    @capture_stdout
    def start_example_0(self, name=ETH0_BACKEND_NAME, addr=ETH0_BACKEND_ADDR):
        print(f"Starting EXAMPLE 0 - default pass-through handler")
        handler = RPCEndpointsHandlerMiddlewareFactory.create_pass_through(addr, name, self.updater)

        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_1(self, rate_1: float, rate_2: float, name=ETH0_BACKEND_NAME, addr=ETH0_BACKEND_ADDR):
        print(f"Starting EXAMPLE 1 - basic priorities handler | request are processed according to their priorities")
        print(f"  priority 0 - full speed")
        print(f"  priority 1 - limited to {rate_1} request/second")
        print(f"  priority 2 - limited to {rate_2} request/second")

        name = name + " prio"
        handler = ExampleHandlerMiddlewareFactory.create_single_endpoint_prio(addr, name, self.updater, rate_1, rate_2)

        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_2(self, name=ETH0_BACKEND_NAME, addr=ETH0_BACKEND_ADDR):
        print(f"Starting EXAMPLE 2 - basic QoS handler | request are routed based on the request method")
        print(f"  other calls          -> endpoint 1")
        print(f"  eth_getBlockByNumber -> endpoint 2")

        handler = ExampleHandlerMiddlewareFactory.create_multi_endpoint_method_qos(addr, name, self.updater)

        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_3(self, name=ETH0_BACKEND_NAME, addr=ETH0_BACKEND_ADDR):
        print(f"Starting EXAMPLE 3 - naive QoS handler | request are spread across endpoints - even requests are "
              f"assigned to endpoint 0, and odd to endpoint 1")

        handler = ExampleHandlerMiddlewareFactory.create_multi_endpoint_interleave_qos(addr, name, self.updater)

        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_4(self, name=ETH0_BACKEND_NAME, addr=ETH0_BACKEND_ADDR):
        print(f"Starting EXAMPLE 4 - simple QoS handler | load is spread evenly across endpoints")

        handler = ExampleHandlerMiddlewareFactory.create_multi_endpoint_load_balancing_qos(addr, name, self.updater)

        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_5(self, rate1: float, rate2: float, name_eth=ETH0_BACKEND_NAME, addr_eth=ETH0_BACKEND_ADDR,
                        name_infura=INFURA_NAME, addr_infura=INFURA_ADDR):
        print(f"Starting EXAMPLE 5 - basic priorities handler | request are processed according to their priorities")
        print(f"  priority 0 - full speed, routed to the local geth endpoint")
        print(f"  priority 1 - limited to {rate1} request/second, routed the to local geth endpoint")
        print(f"  priority 2 - limited to {rate2} request/second, routed to infura endpoint")

        name_infura = name_infura + " prio"
        name_eth = name_eth + " prio"
        upd = self.updater

        handler = ExampleHandlerMiddlewareFactory.create_multi_infura_endpoint_prio(addr_eth, name_eth,
                                                                                    addr_infura, name_infura,
                                                                                    upd, rate1, rate2)

        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_6(self, name_eth=ETH0_BACKEND_NAME, addr_eth=ETH0_BACKEND_ADDR,
                        name_infura=INFURA_NAME, addr_infura=INFURA_ADDR):
        print(f"Starting EXAMPLE 6 - complex priorities handler | request are processed according to their priorities")
        print(f"  priority 0 - full speed with two endpoints; the first one handles: net_version, and the second one "
              f"all other methods")
        print(f"  priority 1 - basic pass-through for all requests routed to the local geth endpoint")
        print(f"  priority 2 - basic pass-through for all requests routed to infura endpoint")

        handler = ExampleHandlerMiddlewareFactory.create_multi_infura_complex_endpoint_prio(addr_eth, name_eth,
                                                                                            addr_infura, name_infura,
                                                                                            self.updater)
        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_7(self, name_eth=ETH0_BACKEND_NAME, addr_eth=ETH0_BACKEND_ADDR,
                        name_infura=INFURA_NAME, addr_infura=INFURA_ADDR):
        print(f"Starting EXAMPLE 7 - arch requests handler | request are routed to an endpoint based on "
              f"the method type")
        print(f"  local eth rpi - all non-archive calls")
        print(f"  infura        - all archive calls")

        handler = ExampleHandlerMiddlewareFactory.create_multi_infura_arch_endpoint_prio(addr_eth, name_eth,
                                                                                         addr_infura, name_infura,
                                                                                         self.updater)
        self.runner_service.run_forever(handler)

    @capture_stdout
    def start_example_8(self, endpoints: List[Tuple[str, str]]):
        print(f"Starting EXAMPLE 8 - Multiple physical backends to handle CPU intensive tasks | "
              f"basic QoS -> load balancing exactly as in example 4 (eth_chainId call automatically returns ethereum)")
        print(f"Provided endpoint addresses:")
        for addr, name in endpoints:
            print(f"    {name} @ {addr}")

        handler = ExampleHandlerMiddlewareFactory.create_multi_device_load_balancing_qos(endpoints, self.updater)

        self.runner_service.run_forever(handler)
