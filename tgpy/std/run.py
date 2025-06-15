"""
name: run
origin: tgpy://builtin_module/run
priority: 550
"""

from pathlib import Path

from pyrogram.errors import MessageNotModified
from pyrogram.types import Message

from tgpy import Context
from tgpy._core.eval_message import eval_message
from tgpy.api.parse_tgpy_message import parse_tgpy_message

ctx: Context


async def run() -> str | None:
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
    try:
        await eval_message(code, original)
    except MessageNotModified:
        # If the result is too long, Telegram may truncate it and return a
        # MessageNotModified error when we try to edit with the same content.
        # Ignore this error so the bot doesn't crash and leave the original
        # message unchanged.
        pass
    return None


__all__ = ['run']