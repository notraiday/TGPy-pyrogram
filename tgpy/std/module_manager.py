"""
name: module_manager
origin: tgpy://builtin_module/module_manager
priority: 800
"""

import io
from dataclasses import dataclass
from textwrap import dedent
from pathlib import Path

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from pyrogram.types.messages_and_media.message_entity import MessageEntity

import tgpy.api
from tgpy.api import Utf16CodepointsWrapper, parse_tgpy_message, tgpy_eval
from tgpy.context import Context
from tgpy.modules import (
    Module,
    delete_module_file,
    deserialize_module,
    get_module_names,
    get_user_modules,
)

ctx: Context

MODULE_NAME = 'module_manager'
IGNORED_MESSAGES_KEY = f'{MODULE_NAME}.ignored_messages'


@dataclass
class GetCodeResult:
    code: str | None = None
    name: str | None = None
    error: str | None = None
    do_eval: bool = False


async def _get_code() -> GetCodeResult:
    msg: Message | None = ctx.msg.reply_to_message
    if msg is None:
        return GetCodeResult(error='Reply to a message or provide code as an argument')
    if msg.document and msg.document.file_name and msg.document.file_name.endswith('.py'):
        data = await msg.download(in_memory=True)
        if hasattr(data, 'getvalue'):
            data = data.getvalue()
        if isinstance(data, (bytes, bytearray)):
            return GetCodeResult(
                data.decode(),
                msg.document.file_name.removesuffix('.py'),
                do_eval=True,
            )
    message_data = parse_tgpy_message(msg)
    if message_data.is_tgpy_message:
        return GetCodeResult(message_data.code, do_eval=not msg.outgoing)
    if msg.text or msg.caption:
        return GetCodeResult(msg.text or msg.caption, do_eval=True)
    return GetCodeResult(error='No code found in reply message')


class ModulesObject:
    async def add(self, name: str | None = None, code: str | None = None) -> str:
        if name is not None:
            name = str(name)

        do_eval = False
        if code is None:
            code_res = await _get_code()
            if code_res.error:
                return code_res.error
            do_eval = code_res.do_eval
            code = code_res.code
            name = name or code_res.name
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

        module = deserialize_module(code, name)
        name = module.name

        if not name:
            return (
                "Couldn't determine module name. Use modules.add('name') to specify it"
            )

        if name in self and module.using_fallback_metadata:
            module = self[name]
            module.code = code
        module.save()

        if do_eval:
            await tgpy_eval(
                module.code,
                filename=module.origin,
                wrap_stdio=False,
            )

        return dedent(
            f"""
            Added {'and executed ' if do_eval else ''}module {module.name!r}.
            Module's code will be executed every time TGPy starts.
            """
        ).strip()

    async def share(self, name: str) -> str | None:
        if name not in self:
            return f'No module named {name!r}'
        module = self[name]
        if len(module.code) > 4096:
            file = io.BytesIO(module.code.encode())
            file.name = module.name + '.py'
            await ctx.msg.reply_document(file)
        else:
            text = Utf16CodepointsWrapper(module.code.strip())
            msg = await ctx.msg.reply_text(
                str(text),
                entities=[
                    MessageEntity(
                        type=MessageEntityType.PRE,
                        offset=0,
                        length=len(text),
                        language='python',
                    )
                ],
            )
            ignored_messages = tgpy.api.config.get(IGNORED_MESSAGES_KEY, [])
            ignored_messages.append([msg.chat.id, msg.id])
            tgpy.api.config.save()
        return None

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
            ).strip()
        return (
            dedent(
                """
            Your modules:
            {}
            
            Change modules with `modules.add(name)` and `modules.remove(name)`.
            Learn more at https://tgpy.dev/extensibility/modules.
            """
            )
            .format(lst)
            .strip()
        )

    def __iter__(self):
        return (mod.name for mod in get_user_modules())

    def __getitem__(self, mod_name):
        return Module.load(mod_name)

    def __contains__(self, mod_name):
        return mod_name in get_module_names()


tgpy.api.variables['modules'] = ModulesObject()


async def exec_hook(message: Message, is_edit: bool):
    ignored_messages = tgpy.api.config.get(IGNORED_MESSAGES_KEY, [])
    return [message.chat.id, message.id] not in ignored_messages


tgpy.api.exec_hooks.add(MODULE_NAME, exec_hook)

__all__ = []
