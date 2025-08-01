"""
name: module_manager
origin: tgpy://builtin_module/module_manager
priority: 800
"""

from datetime import datetime
from textwrap import dedent
from pathlib import Path

from pyrogram.types import Message

import tgpy.api
from tgpy import Context
from tgpy.api import parse_tgpy_message
from tgpy.modules import Module, delete_module_file, get_module_names, get_user_modules
from tgpy.utils import FILENAME_PREFIX

ctx: Context


class ModulesObject:
    async def add(self, name: str, code: str | None = None) -> str:
        name = str(name)

        if code is None:
            original: Message = ctx.msg.reply_to_message
            if original is None:
                return 'Use this function in reply to a message'
            message_data = parse_tgpy_message(original)
            if message_data.is_tgpy_message:
                code = message_data.code
            elif original.document:
                file_path = await original.download()
                try:
                    code = Path(file_path).read_text(encoding='utf-8')
                except Exception:
                    return 'Failed to read file attachment'
            else:
                return 'No code found in reply message'

        origin = f'{FILENAME_PREFIX}module/{name}'

        if name in self:
            module = self[name]
            module.code = code
        else:
            module = Module(
                name=name,
                once=False,
                code=code,
                origin=origin,
                priority=int(datetime.now().timestamp()),
            )
        module.save()

        return dedent(
            f"""
            Added module {name!r}.
            Module's code will be executed every time TGPy starts.
            """
        )

    def remove(self, name) -> str:
        try:
            delete_module_file(name)
        except FileNotFoundError:
            return f'No module named {name!r}.'
        return f'Removed module {name!r}.'

    def __str__(self):
        lst = '\n'.join(
            f'{idx + 1}. {mod.name}' for idx, mod in enumerate(get_user_modules())
        )
        if not lst:
            return dedent(
                """
                You have no modules.
                Learn about modules at https://tgpy.dev/extensibility/modules.
                """
            )
        return dedent(
            """
            Your modules:
            {}
            
            Change modules with `modules.add(name)` and `modules.remove(name)`.
            Learn more at https://tgpy.dev/extensibility/modules.
            """
        ).format(lst)

    def __iter__(self):
        return (mod.name for mod in get_user_modules())

    def __getitem__(self, mod_name):
        return Module.load(mod_name)

    def __contains__(self, mod_name):
        return mod_name in get_module_names()


tgpy.api.variables['modules'] = ModulesObject()

__all__ = []
