import sys
import traceback as tb

import pyrogram
from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.types import Message, MessageEntity
from pyrogram.raw.types import MessageEntityTextUrl

from tgpy import app, reactions_fix
from tgpy.api.utils import Utf16CodepointsWrapper

TITLE = 'TGPy'
RUNNING_TITLE = 'TGPy running'
OLD_TITLE_URLS = ['https://github.com/tm-a-t/TGPy', 'https://tgpy.tmat.me/']
TITLE_URL = 'https://tgpy.dev/'
FORMATTED_ERROR_HEADER = f'<b><a href="{TITLE_URL}">TGPy error&gt;</a></b>'


async def edit_message(
    message: Message,
    code: str,
    result: str | None = '',
    traceback: str = '',
    output: str = '',
    is_running: bool = False,
    result_monospaced: bool = True
) -> Message:
    output_parts = [result, output, traceback]
    if not result and any(output_parts):
        # if result is None, but there is output/traceback, don't show None
        output_parts.pop(0)
    output_parts = [str(x) for x in output_parts]
    output_parts = [x for x in output_parts if x.strip()]
    # make sure there are no trailing spaces
    for i in range(len(output_parts) - 1, -1, -1):
        if not output_parts[i].rstrip():
            output_parts.pop(i)
        else:
            output_parts[i] = output_parts[i].rstrip()
            break

    parts: list[tuple[str, list[MessageEntityType]]] = [
        (code.strip(), [MessageEntityType.PRE]),
        ('\n\n', []),
        (RUNNING_TITLE if is_running else TITLE, [MessageEntityType.BOLD, MessageEntityType.TEXT_LINK]),
    ]
    if output_parts:
        parts.append((' ', []))
        parts.extend(
            [
                (
                    part + ('\n' if i != len(output_parts) - 1 else ''),
                    [MessageEntityType.CODE],
                )
                for i, part in enumerate(output_parts)
            ]
        )

    entities: list[MessageEntity] = []
    offset = 0
    for part, ent_types in parts:
        part = Utf16CodepointsWrapper(part)
        for ent_type in ent_types:
            if ent_type == MessageEntityType.PRE:
                entities.append(
                    MessageEntity(
                        type=MessageEntityType.PRE,
                        offset=offset,
                        length=len(part),
                        language='python',
                    )
                )
            elif ent_type in (MessageEntityType.BOLD, MessageEntityType.CODE):
                entities.append(
                    MessageEntity(type=ent_type, offset=offset, length=len(part))
                )
            elif ent_type == MessageEntityType.TEXT_LINK:
                entities.append(
                    MessageEntity(
                        type=MessageEntityType.TEXT_LINK,
                        offset=offset,
                        length=len(part),
                        url=TITLE_URL,
                    )
                )
            else:
                raise ValueError(f'Unknown entity type {ent_type}')
        offset += len(part)

    text = ''.join(part for part, _ in parts)
    if len(text) > 4096:
        text = text[:4095] + '…'
    for ent in entities:
        if ent.offset >= 4096:
            ent.offset = 0
            ent.length = 0
        elif ent.offset + ent.length > 4096:
            ent.length = 4096 - ent.offset

    # Entity for code block (python)
    entities.append(MessageEntity(
        offset=current_offset, 
        length=len(code_part), 
        type=MessageEntityType.PRE,
        language='python'
    ))
    current_offset += len(code_part) + 2  # +2 for \n\n

    # Entities for the title part of the display line
    title_offset_in_display_line = 0 # Title is at the start of display_line_after_code's construction before result
    
    # Bold title
    entities.append(MessageEntity(
        offset=current_offset + title_offset_in_display_line,
        length=len(title_text_part),
        type=MessageEntityType.BOLD
    ))
    # Clickable title
    # entities.append(MessageEntity(
    #     offset=current_offset + title_offset_in_display_line,
    #     length=len(title_text_part),
    #     type=MessageEntityType.TEXT_LINK,
    #     url=TITLE_URL
    # ))

    # Entity for the result part (after title and a space)
    result_offset_in_display_line = len(title_text_part) + 1 # +1 for space after title
    if len(result_text_part) > 0 and result_monospaced: # Only add if there's a result
        entities.append(MessageEntity(
            offset=current_offset + result_offset_in_display_line,
            length=len(result_text_part),
            type=MessageEntityType.CODE # Result is in a code block
        ))
    
    current_offset += len(display_line_after_code) + 2 # +2 for \n\n

    # Entities for output and traceback if they exist
    if output.strip():
        entities.append(MessageEntity(
            offset=current_offset,
            length=len(text_parts[2]), # output part
            type=MessageEntityType.CODE
        ))
        current_offset += len(text_parts[2]) + 2 # +2 for \n\n
    
    if traceback.strip():
        # The last part might not have \n\n after it depending on construction
        entities.append(MessageEntity(
            offset=current_offset,
            length=len(text_parts[-1]), # traceback part (or output if no traceback)
            type=MessageEntityType.CODE
        ))

    # Construct final text
    # First part (code) is followed by \n\n
    # Second part (title + result) is followed by \n\n
    # Subsequent parts (output, traceback) are also followed by \n\n, except the last one
    
    final_text_str = code_part + '\n\n' + display_line_after_code
    if output.strip():
        final_text_str += '\n\n' + text_parts[2]
    if traceback.strip():
        final_text_str += '\n\n' + text_parts[-1] # This will be traceback, or output if no traceback

    if len(final_text_str) > 4096: # Telegram's message length limit
        # A more sophisticated truncation that preserves entities might be needed
        # For now, simple string truncation. Pyrogram might handle entities with truncated text.
        final_text_str = final_text_str[:4095] + '…'
        # Adjust entities if truncation happens. This is complex.
        # Pyrogram might handle this gracefully, or entities might become invalid.
        # For simplicity, we'll rely on Pyrogram's behavior for now.
        # A robust solution would filter/adjust entities whose offsets are beyond the new length.
        valid_entities = []
        for e in entities:
            if e.offset < len(final_text_str):
                e.length = min(e.length, len(final_text_str) - e.offset)
                valid_entities.append(e)
        entities = valid_entities


    # Pyrogram's edit uses message.edit_text
    res = await message.edit_text(
        text=str(text),
        entities=entities,
        link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
    )
    reactions_fix.update_hash(res, in_memory=False)
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


async def send_error(chat_id_or_username) -> None:
    exc = ''.join(tb.format_exception(*sys.exc_info()))
    if len(exc) > 4000:
        exc = exc[:3950] + '…'

    await app.client.send_message(
        chat_id=chat_id_or_username,
        text=f'{FORMATTED_ERROR_HEADER}\n\n<code>{exc}</code>',
        link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        parse_mode=ParseMode.HTML,
    )


__all__ = [
    'Utf16CodepointsWrapper',
    'edit_message',
    'send_error',
    'get_title_entity',
]
