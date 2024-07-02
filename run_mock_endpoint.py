from tests.web3pi_proxy.tools.mock_endpoint import MockEndpoint

if __name__ == "__main__":
    print("Starting mock node")
    MockEndpoint().run_forever()
