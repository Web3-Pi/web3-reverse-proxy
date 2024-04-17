# FIXME: a general architecture hint: https://web3py.readthedocs.io/en/stable/internals.html
import os
import sys


if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from web3_reverse_proxy.service.rpcproxyservice import DefaultRPCProxyService


def main():
    # DefaultRPCProxyService.launch_service()
    DefaultRPCProxyService.launch_hack_mt_service(6512, "rpi5d.local", 8545, 50)


if __name__ == '__main__':
    main()
