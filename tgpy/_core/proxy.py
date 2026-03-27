"""Resolve Pyrogram proxy settings from CLI, env, and config."""

import logging
import os
from urllib.parse import unquote, urlparse

from tgpy.api.config import config

logger = logging.getLogger(__name__)

_PROXY_ENV_KEYS = (
    'TGPY_PROXY',
    'HTTPS_PROXY',
    'https_proxy',
    'HTTP_PROXY',
    'http_proxy',
)


def parse_proxy_url(url: str) -> dict | None:
    """Build a Pyrogram ``proxy`` dict from a URL, or ``None`` if invalid."""
    text = url.strip()
    if not text:
        return None
    parsed = urlparse(text)
    scheme = (parsed.scheme or '').lower()
    if scheme == 'https':
        scheme = 'http'
    if scheme not in ('socks5', 'socks4', 'http'):
        return None
    hostname = parsed.hostname
    if not hostname:
        return None
    port = parsed.port
    if port is None:
        port = 1080 if scheme.startswith('socks') else 8080
    result: dict = {'scheme': scheme, 'hostname': hostname, 'port': int(port)}
    if parsed.username:
        result['username'] = unquote(parsed.username)
    if parsed.password is not None:
        result['password'] = unquote(parsed.password)
    return result


def normalize_config_proxy(cfg: dict) -> dict | None:
    """Map ``core.proxy`` from config YAML to Pyrogram's ``proxy`` dict."""
    if not cfg or not isinstance(cfg, dict):
        return None
    scheme = cfg.get('scheme') or cfg.get('proxy_type')
    hostname = cfg.get('hostname') or cfg.get('addr')
    if not scheme or not hostname:
        return None
    scheme = str(scheme).lower()
    if scheme == 'https':
        scheme = 'http'
    if scheme not in ('socks5', 'socks4', 'http'):
        logger.warning('Unsupported proxy_type %r in config', scheme)
        return None
    port = cfg.get('port')
    if port is None:
        port = 1080 if scheme.startswith('socks') else 8080
    out: dict = {'scheme': scheme, 'hostname': str(hostname), 'port': int(port)}
    if cfg.get('username') is not None:
        out['username'] = str(cfg['username'])
    if cfg.get('password') is not None:
        out['password'] = str(cfg['password'])
    return out


def resolve_telegram_proxy(cli_proxy_url: str | None) -> dict | None:
    """
    Order: ``--proxy`` / ``cli_proxy_url``, then env (``TGPY_PROXY``,
    ``HTTPS_PROXY``, …), then ``core.proxy`` in config.
    """
    if cli_proxy_url is not None and cli_proxy_url.strip():
        proxy = parse_proxy_url(cli_proxy_url)
        if not proxy:
            raise ValueError(f'Invalid --proxy URL: {cli_proxy_url!r}')
        return proxy

    for key in _PROXY_ENV_KEYS:
        raw = os.getenv(key)
        if not raw:
            continue
        proxy = parse_proxy_url(raw)
        if proxy:
            logger.debug('Telegram proxy from %s', key)
            return proxy
        logger.warning('Ignoring invalid proxy URL in %s', key)

    cfg = config.get('core.proxy')
    if cfg:
        normalized = normalize_config_proxy(cfg)
        if normalized:
            return normalized
    return None
