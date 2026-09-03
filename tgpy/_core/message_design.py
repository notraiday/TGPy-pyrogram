import sys
import traceback as tb
from copy import copy

import pyrogram
from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.types import Message, MessageEntity

from tgpy import app, reactions_fix
from tgpy.api.utils import Utf16CodepointsWrapper

TITLE = 'TGPy'
RUNNING_TITLE = 'TGPy running'
OLD_TITLE_URLS = ['https://github.com/tm-a-t/TGPy', 'https://tgpy.tmat.me/']
TITLE_URL = 'https://tgpy.dev/'
FORMATTED_ERROR_HEADER = '<b>TGPy error&gt;</b>'


def _truncate_utf16(text: str, max_length: int) -> Utf16CodepointsWrapper:
    wrapped_text = Utf16CodepointsWrapper(text)
    if len(wrapped_text) <= max_length:
        return wrapped_text

    prefix = text.encode('utf-16-le')[: (max_length - 1) * 2]
    while True:
        try:
            decoded_prefix = prefix.decode('utf-16-le')
            break
        except UnicodeDecodeError:
            prefix = prefix[:-2]
    return Utf16CodepointsWrapper(f'{decoded_prefix}…')


async def edit_message(
    message: Message,
    code: str,
    result: str | None = '',
    traceback: str = '',
    output: str = '',
    is_running: bool = False,
    result_monospaced: bool = True,
    result_entitites_rewrite: list[MessageEntity] | None = None,
) -> Message:
    display_parts = [
        Utf16CodepointsWrapper(str(part).strip())
        for part in (result, output, traceback)
        if part is not None and str(part).strip()
    ]
    inline_result = display_parts[0] if display_parts else Utf16CodepointsWrapper('')
    trailing_parts = display_parts[1:]

    code_part = Utf16CodepointsWrapper(code.strip())
    title_part = Utf16CodepointsWrapper((RUNNING_TITLE if is_running else TITLE) + '>')
    title_line = Utf16CodepointsWrapper(title_part)
    if inline_result:
        title_line = Utf16CodepointsWrapper(f'{title_part} {inline_result}')

    text_parts = [code_part, title_line, *trailing_parts]
    final_text_str = Utf16CodepointsWrapper('\n\n'.join(text_parts))

    entities = [
        MessageEntity(
            offset=0,
            length=len(code_part),
            type=MessageEntityType.PRE,
            language='python',
        ),
        MessageEntity(
            offset=len(code_part) + 2,
            length=len(title_part),
            type=MessageEntityType.BOLD,
        ),
    ]

    current_offset = len(code_part) + 2 + len(title_part)
    if inline_result:
        current_offset += 1
        if result_entitites_rewrite is not None:
            for entity in result_entitites_rewrite:
                shifted_entity = copy(entity)
                shifted_entity.offset += current_offset
                entities.append(shifted_entity)
        elif result_monospaced:
            entities.append(
                MessageEntity(
                    offset=current_offset,
                    length=len(inline_result),
                    type=MessageEntityType.CODE,
                )
            )
        current_offset += len(inline_result)

    for part in trailing_parts:
        current_offset += 2
        entities.append(
            MessageEntity(
                offset=current_offset,
                length=len(part),
                type=MessageEntityType.CODE,
            )
        )
        current_offset += len(part)

    if len(final_text_str) > 4096:
        final_text_str = _truncate_utf16(final_text_str, 4096)
        valid_entities = []
        for entity in entities:
            if entity.offset < len(final_text_str):
                entity.length = min(entity.length, len(final_text_str) - entity.offset)
                valid_entities.append(entity)
        entities = valid_entities

    res = await message.edit_text(
        text=str(final_text_str),  # Ensure it's a plain str
        entities=entities,
        link_preview_options=pyrogram.types.LinkPreviewOptions(
            is_disabled=True
        ),  # Equivalent to link_preview=False
    )
    reactions_fix.update_hash(res, in_memory=False)  # Ensure res is Pyrogram Message
    return res


def get_title_entity(message: Message) -> MessageEntity | None:
    for e in message.entities or []:
        if (
            e.type == MessageEntityType.TEXT_LINK
            and e.url
            and (e.url in OLD_TITLE_URLS or e.url == TITLE_URL)
        ):
            return e
    return None


def get_united_code_entity(message: Message) -> MessageEntity | None:
    last_entity = None
    if message.entities:  # Check if entities exist
        for e in message.entities:
            # Pyrogram uses e.type and e.language
            if e.type == MessageEntityType.PRE and e.language == 'python':
                if not last_entity:
                    last_entity = e
                elif last_entity.offset + last_entity.length + 1 == e.offset:
                    # If the previous entity is contiguous with the current one, merge them
                    last_entity.length += e.length + 1

    return last_entity


async def send_error(
    chat_id_or_username,
) -> None:  # Parameter can be chat_id or username
    exc = ''.join(tb.format_exception(*sys.exc_info()))
    if len(exc) > 4000:  # Keep it within reasonable limits for a message
        exc = exc[:3950] + '…'  # Adjusted for header and code tags

    # Pyrogram's send_message
    # parse_mode is an enum
    await app.client.send_message(
        chat_id=chat_id_or_username,
        text=f'{FORMATTED_ERROR_HEADER}\n\n<code>{exc}</code>',
        link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        parse_mode=ParseMode.HTML,
    )


__all__ = [
    'Utf16CodepointsWrapper',  # Added Utf16CodepointsWrapper to __all__
    'edit_message',
    'send_error',
    'get_title_entity',  # Added get_title_entity to __all__
]
