import asyncio
import logging
import os
import platform
import subprocess
import sys

import aiorun
import yaml
from pyrogram import Client, errors
from rich.console import Console, Theme
from yaml import YAMLError

from tgpy import __version__ as tgpy_version
from tgpy import app
from tgpy._handlers import add_handlers
from tgpy.api import DATA_DIR, MODULES_DIR, WORKDIR, config
from tgpy.modules import run_modules, serialize_module
from tgpy.utils import SESSION_FILENAME, create_config_dirs

logger = logging.getLogger(__name__)

theme = Theme(inherit=False)
console = Console(theme=theme)


async def ainput(prompt: str, password: bool = False):
    def wrapper(prompt, password):
        return console.input(prompt, password=password)

    return await asyncio.get_event_loop().run_in_executor(
        None, wrapper, prompt, password
    )


def get_api_id() -> int | None:
    api_id = os.getenv('TGPY_API_ID') or config.get('core.api_id')
    return int(api_id) if api_id else None


def get_api_hash() -> str | None:
    return os.getenv('TGPY_API_HASH') or config.get('core.api_hash')


def create_client():
    device_model = None
    if sys.platform == 'linux':
        if os.path.isfile('/sys/devices/virtual/dmi/id/product_name'):
            with open('/sys/devices/virtual/dmi/id/product_name') as f:
                device_model = f.read().strip()
    elif sys.platform == 'darwin':
        device_model = (
            subprocess.check_output('sysctl -n hw.model'.split(' ')).decode().strip()
        )
    elif sys.platform == 'win32':
        device_model = ' '.join(
            subprocess.check_output('wmic computersystem get manufacturer,model')
            .decode()
            .replace('Manufacturer', '')
            .replace('Model', '')
            .split()
        )

    client = Client(
        str(SESSION_FILENAME),
        get_api_id(),
        get_api_hash(),
        device_model=device_model,
        system_version=platform.platform(),
        app_version=f'TGPy {tgpy_version}',
        lang_code='en',
        workdir=str(WORKDIR),
    )
    return client


async def start_client():
    await app.client.start()


async def initial_setup():
    console.print('[bold #ffffff on #16a085] Welcome to TGPy ')
    console.print('Starting setup...')
    console.print()
    console.print('[bold #7f8c8d on #ffffff] Step 1 of 2 ')
    console.print(
        "│ TGPy uses Telegram API, so you'll need to register your Telegram app.\n"
        '│  [#1abc9c]1.[/] Go to https://my.telegram.org\n'
        '│  [#1abc9c]2.[/] Login with your Telegram account\n'
        '│  [#1abc9c]3.[/] Go to "API development tools"\n'
        '│  [#1abc9c]4.[/] Create your app. Choose any app title and short_title. You can leave other fields empty.\n'
        '│ You will get api_id and api_hash.'
    )
    success = False
    while not success:
        try:
            api_id_input = await ainput('│ Please enter api_id: ')
            api_hash_input = await ainput('│ ...and api_hash: ')
            if not api_id_input or not api_hash_input:
                console.print(
                    '│ [bold #ffffff on #ed1515]API ID and API Hash cannot be empty. Please try again.'
                )
                continue
            config.set('core.api_id', int(api_id_input))
            config.set('core.api_hash', api_hash_input)

            temp_client = Client(
                name='tgpy_setup_check',
                api_id=int(api_id_input),
                api_hash=api_hash_input,
                in_memory=True,
            )
            console.print()
            console.print('[bold #7f8c8d on #ffffff] Step 2 of 2 ')
            console.print('│ Now login to Telegram.')

            await temp_client.connect()
            await temp_client.disconnect()
            success = True
        except errors.ApiIdInvalid:
            console.print(
                '│ [bold #ffffff on #ed1515]Incorrect api_id/api_hash, try again'
            )
        except ValueError:
            console.print(
                '│ [bold #ffffff on #ed1515]api_id must be an integer. Please try again.'
            )
        except Exception as e:
            console.print(
                f'│ [bold #ffffff on #ed1515]An error occurred: {e}. Please try again.'
            )
            if os.path.exists(f'{WORKDIR}/{SESSION_FILENAME}.session'):
                os.remove(f'{WORKDIR}/{SESSION_FILENAME}.session')
    console.print('│ Login successful (API credentials validated)!')
    console.print('│ You will be prompted to log in on the first run if needed.')


def migrate_hooks_to_modules():
    old_modules_dir = DATA_DIR / 'hooks'
    if not old_modules_dir.exists():
        return
    for mod_file in old_modules_dir.iterdir():
        try:
            if mod_file.suffix not in ['.yml', '.yaml']:
                continue
            try:
                with open(mod_file) as f:
                    module = yaml.safe_load(f)

                if 'type' in module:
                    del module['type']
                if 'datetime' in module:
                    module['priority'] = int(module['datetime'].timestamp())
                    del module['datetime']

                new_mod_file = mod_file.with_suffix('.py')
                with open(new_mod_file, 'w') as f:
                    f.write(serialize_module(module))
                mod_file.unlink()
                mod_file = new_mod_file
            except YAMLError:
                continue
        except Exception:
            pass
        finally:
            mod_file.rename(MODULES_DIR / mod_file.name)
    old_modules_dir.rmdir()


def migrate_config():
    if old_api_id := config.get('api_id'):
        config.set('core.api_id', int(old_api_id))
        config.unset('api_id')
    if old_api_hash := config.get('api_hash'):
        config.set('core.api_hash', old_api_hash)
        config.unset('api_hash')


async def _async_main():
    create_config_dirs()
    os.chdir(WORKDIR)
    migrate_hooks_to_modules()

    config.load()
    migrate_config()
    if not (get_api_id() and get_api_hash()):
        await initial_setup()

    logger.info('Starting TGPy...')
    app.client = create_client()
    add_handlers(app.client)
    await start_client()
    logger.info('TGPy is running!')
    await run_modules()
    from pyrogram import idle

    try:
        await idle()
    except (KeyboardInterrupt, SystemExit):
        logger.info('Received shutdown signal, cleaning up...')

    # Cleanup
    logger.info('Stopping Telegram client...')
    await app.client.stop()
    logger.info('TGPy shutdown complete')


async def async_main():
    try:
        await _async_main()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received, exiting...')
    except Exception:
        logger.exception('TGPy failed to start')
    finally:
        # Make sure we stop the event loop in any case
        if app.client and app.client.is_connected:
            await app.client.stop()
        asyncio.get_event_loop().stop()


def main():
    try:
        aiorun.run(async_main(), stop_on_unhandled_errors=True)
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received, exiting...')
