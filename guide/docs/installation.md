---
description: You can install TGPy with uv and run it with a shell command. To update TGPy, use update() function.
---

# Installation

TGPy is a command line application that connects to your account much like a Telegram app on a new device.

You can install and run TGPy on your computer, but you might have to use a remote server to have TGPy available 24/7.

!!! warning

    **Make sure you run TGPy on a trusted machine** — that is, no one except you can read TGPy files on the computer.
    Anyone with access to TGPy files can steal your Telegram account.

    And the other way round: anyone with access to your Telegram account has access to the machine TGPy is running on.

It’s recommended to use [uv](https://docs.astral.sh/uv/) or Docker.

## How to install using uv

1. Make sure you have [Python 3.14 or above](https://www.python.org/) installed.

2. Install uv if you don’t have it:

    === "Linux and macOS"

        ```shell
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

    === "Windows"

        ```powershell
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        ```

3. Install TGPy:

    ```shell
    uv tool install tgpy
    ```

4. Start it:

    ```shell
    tgpy
    ```


Follow the instructions to connect your Telegram account for the first time. When it’s ready, try sending `ping()` to any chat to check if TGPy is running.

## How to install using Docker

```shell
docker pull tgpy/tgpy
docker run -it --rm -v /tgpy_data:/data tgpy/tgpy
```

Follow the instructions to connect your Telegram account for the first time. When it’s ready, try sending `ping()` to any chat to check if TGPy is running.

## Updating to the latest version

When new updates arrive, you can get them with a TGPy function or from  shell.

=== "From Telegram message"

    ```python
    update()
    ```

=== "From shell using uv"

    ```shell
    uv tool upgrade tgpy
    ```

=== "From shell using docker"

    ```shell
    docker pull tgpy/tgpy
    ```
   
    Then re-run:

    ```shell
    docker run -it --rm -v /tgpy_data:/data tgpy/tgpy
    ```

## Running in background

To get TGPy running in background, you need to additionally configure systemd, docker compose, or similar.
Instructions are coming.

## Data storage

Config, session, and modules are stored in `~/.config/tgpy` directory (unless you’re using Docker.) 
You can change this path via `TGPY_DATA` environment variable.

## Using proxy

You can point TGPy at a proxy in three ways (highest priority first):

1. **CLI:** `tgpy --proxy socks5://127.0.0.1:1080` (also `socks4://` or `http://`).
2. **Environment:** `TGPY_PROXY`, or standard `HTTPS_PROXY` / `https_proxy` / `HTTP_PROXY` / `http_proxy` with the same URL form (credentials may be included, e.g. `socks5://user:pass@host:port`).
3. **Config file** (below).

If you use only `config.yml`, do the following:

1. Launch TGPy and provide api_id and api_hash, then quit.
2. Open `config.yml` file (see Data storage above) and add your proxy settings here:
   ```yaml
   core:
       api_hash: ...
       api_id: ...
       proxy:
           proxy_type: socks5
           addr: ...
           port: ...
           username: ...
           password: ...
   ```
3. Run TGPy normally

## API secrets as environment variables

It's possible to provide Telegram API ID and hash through environment variables `TGPY_API_ID` and `TGPY_API_HASH`.
