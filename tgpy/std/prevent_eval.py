"""
    name: prevent_eval
    origin: tgpy://builtin_module/prevent_eval
    priority: 400
"""

import re

from pyrogram import Client as TelegramClient
from pyrogram.enums import MessageServiceType
from pyrogram.types import Message

import tgpy.api
from tgpy import Context, reactions_fix
from tgpy._core.eval_message import running_messages

client: TelegramClient
ctx: Context

MODULE_NAME = 'prevent_eval'
IGNORED_MESSAGES_KEY = f'{MODULE_NAME}.ignored_messages'
CANCEL_RGX = re.compile(r'(?i)^(cancel|сфтсуд)$')
INTERRUPT_RGX = re.compile(r'(?i)^(stop|ыещз)$')


async def cancel_message(message: Message, permanent: bool = True) -> bool:
    parsed = tgpy.api.parse_tgpy_message(message)

    if task := running_messages.get((message.chat.id, message.id)):
        task.cancel()
    if not parsed.is_tgpy_message:
        return False
    message = await message.edit_text(parsed.code)

    if permanent:
        ignored_messages = tgpy.api.config.get(IGNORED_MESSAGES_KEY, [])
        ignored_messages.append([message.chat.id, message.id]) 
        tgpy.api.config.save()
    else:
        reactions_fix.update_hash(message)

    return True


async def handle_cancel(message: Message, permanent: bool = True):
    target: Message | None = message.reply_to_message
    thread_id = None

    if (
        target
        and target.forward_origin.sender_user
        and target.forward_origin.sender_user.id == target.from_user.id
        and target.forward_origin.chat.sender_chat and target.forward_origin.chat.sender_chat.id == target.from_user.id
    ):
        # Message from bound channel. Probably sent cancel from comments.
        # Searching for messages to cancel only in this comment thread
        thread_id = target.id
        target = None

    if (
        target
        and hasattr(target, 'service') and target.service
        and hasattr(target, 'service_type') and target.service_type == MessageServiceType.TOPIC_CREATE
    ):
        # Message sent to a topic (without replying to any other message).
        # Searching for messages to cancel only in this topic
        thread_id = target.id
        target = None

    if not target:
        async for msg in client.get_chat_history(
            message.chat.id, limit=10, offset_id=message.id, replies=thread_id
        ):
            if not msg.outgoing:  # Changed from msg.out to msg.outgoing
                continue
            parsed = tgpy.api.parse_tgpy_message(msg)
            if parsed.is_tgpy_message:
                target = msg
                break

    if not target:
        return

    if await cancel_message(target, permanent):
        await message.delete()


async def handle_comment(message: Message):
    ignored_messages = tgpy.api.config.get(IGNORED_MESSAGES_KEY, [])
    ignored_messages.append([message.chat.id, message.id]) 
    tgpy.api.config.save()

    entities = message.entities or []
    for ent in entities:
        if ent.offset < 2:
            ent.length -= 2 - ent.offset
            ent.offset = 0
        else:
            ent.offset -= 2
    await message.edit_text(message.text[2:], entities=entities)  


async def exec_hook(message: Message, is_edit: bool):
    ignored_messages = tgpy.api.config.get(IGNORED_MESSAGES_KEY, [])
    if [message.chat.id, message.id] in ignored_messages:
        return False

    is_comment = message.text.startswith('//') and message.text[2:].strip() if message.text else False
    is_cancel = CANCEL_RGX.fullmatch(message.text) is not None if message.text else False
    is_interrupt = INTERRUPT_RGX.fullmatch(message.text) is not None if message.text else False
    if not is_comment and not is_cancel and not is_interrupt:
        return True

    if is_cancel or is_interrupt:
        await handle_cancel(message, permanent=is_cancel)
    elif is_comment:
        await handle_comment(message)

    return False


tgpy.api.exec_hooks.add(MODULE_NAME, exec_hook)

__all__ = []
