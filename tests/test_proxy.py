import pytest

from tgpy._core import proxy as proxy_mod
from tgpy._core.proxy import (
    normalize_config_proxy,
    parse_proxy_url,
    resolve_telegram_proxy,
)


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        (
            'socks5://127.0.0.1',
            {'scheme': 'socks5', 'hostname': '127.0.0.1', 'port': 1080},
        ),
        (
            'socks5://127.0.0.1:9000',
            {'scheme': 'socks5', 'hostname': '127.0.0.1', 'port': 9000},
        ),
        (
            'http://proxy.example:8888',
            {'scheme': 'http', 'hostname': 'proxy.example', 'port': 8888},
        ),
        (
            'https://proxy.example:8888',
            {'scheme': 'http', 'hostname': 'proxy.example', 'port': 8888},
        ),
        (
            'socks5://user:pass@10.0.0.1:1080',
            {
                'scheme': 'socks5',
                'hostname': '10.0.0.1',
                'port': 1080,
                'username': 'user',
                'password': 'pass',
            },
        ),
        (
            'socks5://us%3Aer:p%40ss@10.0.0.1:1080',
            {
                'scheme': 'socks5',
                'hostname': '10.0.0.1',
                'port': 1080,
                'username': 'us:er',
                'password': 'p@ss',
            },
        ),
    ],
)
def test_parse_proxy_url_ok(url, expected):
    assert parse_proxy_url(url) == expected


@pytest.mark.parametrize(
    'url',
    ['', '   ', 'ftp://x:1', 'socks5://', 'http://'],
)
def test_parse_proxy_url_invalid(url):
    assert parse_proxy_url(url) is None


def test_normalize_config_proxy_maps_keys():
    assert normalize_config_proxy({
        'proxy_type': 'socks5',
        'addr': '1.2.3.4',
        'port': 1000,
    }) == {'scheme': 'socks5', 'hostname': '1.2.3.4', 'port': 1000}


def test_resolve_order_cli_over_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('HTTPS_PROXY', 'socks5://env-host:9999')
    assert resolve_telegram_proxy('socks5://cli:1080') == {
        'scheme': 'socks5',
        'hostname': 'cli',
        'port': 1080,
    }


def test_resolve_env_https_proxy(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('HTTPS_PROXY', 'socks5://p.example:9000')
    assert resolve_telegram_proxy(None) == {
        'scheme': 'socks5',
        'hostname': 'p.example',
        'port': 9000,
    }


def test_resolve_fallback_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in proxy_mod._PROXY_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    cfg_file = tmp_path / 'config.yml'
    cfg_file.write_text(
        'core:\n  proxy:\n    proxy_type: socks5\n    addr: cfg.host\n    port: 7\n'
    )
    from tgpy.api.config import Config

    cfg = Config(config_filename=cfg_file)
    cfg.load()
    monkeypatch.setattr(proxy_mod, 'config', cfg)
    assert resolve_telegram_proxy(None) == {
        'scheme': 'socks5',
        'hostname': 'cfg.host',
        'port': 7,
    }


def test_resolve_invalid_cli_raises():
    with pytest.raises(ValueError, match='Invalid'):
        resolve_telegram_proxy('not-a-url')
