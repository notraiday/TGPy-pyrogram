import logging
from typing import Callable

from pyrogram import Client, filters
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.types import Chat, Message

import tgpy.api
from tgpy import app, reactions_fix
from tgpy._core import message_design
from tgpy._core.eval_message import eval_message, running_messages
from tgpy.api.parse_code import parse_code
from tgpy.api.transformers import exec_hooks
from tgpy.reactions_fix import ReactionsFixResult

logger = logging.getLogger(__name__)

async def outgoing_filter(_, client: Client, message: Message):
    return ((message.chat.id == client.me.id and message.from_user.id == client.me.id) or message.outgoing) and message.from_user and not message.from_user.is_bot

def _handle_errors(func: Callable):
    async def result(client, message: Message):
        try:
            await func(client, message)
        except Exception:
            await message_design.send_error(message.chat.id)

    return result


async def handle_message(
    original_message: Message, *, only_show_warning: bool = False, client=None
) -> None:
    try:
        if not original_message.text and not original_message.caption:
            return
        message_data = tgpy.api.parse_tgpy_message(original_message)

        if message_data.is_tgpy_message:
            # message was edited/tgpy-formatted text was sent

            if not (message := await exec_hooks.apply(original_message, is_edit=True)):
                return

            # if message was "broken" by a hook, return
            message_data = tgpy.api.parse_tgpy_message(message)
            if not message_data.is_tgpy_message:
                return

            code = message_data.code
        else:
            # a new message was sent/message was edited to code

            if not (message := await exec_hooks.apply(original_message, is_edit=False)):
                reactions_fix.update_hash(message, in_memory=True)
                return

            res = await parse_code(message.text or message.caption)
            if not res.is_code:
                reactions_fix.update_hash(message, in_memory=True)
                return

            code = message.text or message.caption

        if only_show_warning:
            await message_design.edit_message(
                message, code, 'Edit message again to evaluate'
            )
        else:
            await eval_message(code, message)
    except Exception as e:
        # Log the error and return
        logger.exception(f"Error handling message: {e}")
        try:
            await message_design.send_error(original_message.chat.id)
        except:
            # If sending error message fails, just log it
            logger.exception("Failed to send error message")


@_handle_errors
async def on_new_message_handler(client, message: Message) -> None:
    # We only handle messages from our own account (outgoing_filter already ensured this)
    await handle_message(message, client=client)


@_handle_errors
async def on_message_edited_handler(client, message: Message) -> None:
    # We only want to process messages from our own account, which is what outgoing_filter already ensures
    # For edited messages, we add an additional check for channel messages
    if message.chat and message.chat.type == "channel" and message.chat.is_broadcast:
        # Don't allow editing in channels, as there are complications with permission checks
        return
    if (message.chat.id, message.id) in running_messages:
        # Message is already running, editing should do nothing.
        # The message will be corrected on the next flush or after evaluation finishes.
        return

    reactions_fix_result = reactions_fix.check_hash(message)

    if reactions_fix_result == ReactionsFixResult.ignore:
        return
    elif reactions_fix_result == ReactionsFixResult.show_warning:
        await handle_message(message, only_show_warning=True, client=client)
        return
    elif reactions_fix_result == ReactionsFixResult.evaluate:
        pass
    else:
        raise ValueError(f'Bad reactions fix result: {reactions_fix_result}')

    await handle_message(message, client=client)


def add_handlers(client):
    client.add_handler(MessageHandler(on_new_message_handler, filters.create(outgoing_filter)))
    client.add_handler(EditedMessageHandler(on_message_edited_handler, filters.create(outgoing_filter)))
