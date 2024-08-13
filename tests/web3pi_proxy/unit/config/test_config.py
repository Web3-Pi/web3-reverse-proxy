import pytest

from web3pi_proxy.config.conf import AppConfig


@pytest.fixture
def config():
    return AppConfig()


class TestProxyConnectionAddress:
    def test_connection_address_set(self, config: AppConfig):
        config.PROXY_CONNECTION_ADDRESS = "my.address"
        assert config.proxy_connection_address == config.PROXY_CONNECTION_ADDRESS

    def test_listen_address_set(self, config: AppConfig):
        config.PROXY_LISTEN_ADDRESS = "127.0.0.1"
        assert config.proxy_connection_address == config.PROXY_LISTEN_ADDRESS

    def test_listen_address_set_ipv6(self, config: AppConfig):
        config.PROXY_LISTEN_ADDRESS = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        assert config.proxy_connection_address == config.PROXY_LISTEN_ADDRESS

    def test_listen_address_any(self, config: AppConfig):
        config.PROXY_LISTEN_ADDRESS = "0.0.0.0"
        assert config.proxy_connection_address == "127.0.0.1"

    def test_listen_address_any_ipv6(self, config: AppConfig):
        config.PROXY_LISTEN_ADDRESS = "::"
        assert config.proxy_connection_address == "::1"

class TestAdminConnectionAddress:
    def test_connection_address_set(self, config: AppConfig):
        config.ADMIN_CONNECTION_ADDRESS = "my.address"
        assert config.admin_connection_address == config.ADMIN_CONNECTION_ADDRESS

    def test_listen_address_set(self, config: AppConfig):
        config.ADMIN_LISTEN_ADDRESS = "127.0.0.1"
        assert config.admin_connection_address == config.ADMIN_LISTEN_ADDRESS

    def test_listen_address_set_ipv6(self, config: AppConfig):
        config.ADMIN_LISTEN_ADDRESS = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        assert config.admin_connection_address == config.ADMIN_LISTEN_ADDRESS

    def test_listen_address_any(self, config: AppConfig):
        config.ADMIN_LISTEN_ADDRESS = "0.0.0.0"
        assert config.admin_connection_address == "127.0.0.1"

    def test_listen_address_any_ipv6(self, config: AppConfig):
        config.ADMIN_LISTEN_ADDRESS = "::"
        assert config.admin_connection_address == "::1"
