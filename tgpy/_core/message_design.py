import sys
import traceback as tb

import pyrogram
from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.types import Message, MessageEntity

from tgpy import app, reactions_fix

TITLE = 'TGPy'
RUNNING_TITLE = 'TGPy running'
OLD_TITLE_URL = 'https://github.com/tm-a-t/TGPy'
TITLE_URL = 'https://tgpy.tmat.me/'
FORMATTED_ERROR_HEADER = f'<b>TGPy error&gt;</b>'


class Utf16CodepointsWrapper(str):
    def __len__(self):
        return len(self.encode('utf-16-le')) // 2

    def __getitem__(self, item):
        s = self.encode('utf-16-le')
        if isinstance(item, slice):
            item = slice(
                item.start * 2 if item.start else None,
                item.stop * 2 if item.stop else None,
                item.step * 2 if item.step else None,
            )
            s = s[item]
        elif isinstance(item, int):
            s = s[item * 2 : item * 2 + 2]
        else:
            raise TypeError(f'{type(item)} is not supported')
        return s.decode('utf-16-le')


async def edit_message(
    message: Message,
    code: str,
    result: str = '',
    traceback: str = '',
    output: str = '',
    is_running: bool = False,
) -> Message:
    if not result and output:
        result = output
        output = ''
    if not result and traceback:
        result = traceback
        traceback = ''

    current_title = (RUNNING_TITLE if is_running else TITLE) + '>'
    
    # Ensure all parts are Utf16CodepointsWrapper for consistent length calculation
    code_part = Utf16CodepointsWrapper(code.strip())
    # The title part itself should not be part of the entity that gets the language 'python'
    # The structure is: code_part \n\n title_part result_part \n\n output_part \n\n traceback_part
    
    title_text_part = Utf16CodepointsWrapper(current_title)
    result_text_part = Utf16CodepointsWrapper(str(result).strip())
    
    # Combined title and result for display line
    display_line_after_code = Utf16CodepointsWrapper(f'{title_text_part} {result_text_part}')

    text_parts = [code_part, display_line_after_code]
    if output.strip():
        text_parts.append(Utf16CodepointsWrapper(output.strip()))
    if traceback.strip():
        text_parts.append(Utf16CodepointsWrapper(traceback.strip()))

    entities = []
    current_offset = 0

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
    if len(result_text_part) > 0 : # Only add if there's a result
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
        text=str(final_text_str), # Ensure it's a plain str
        entities=entities, 
        link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True) # Equivalent to link_preview=False
    )
    reactions_fix.update_hash(res, in_memory=False) # Ensure res is Pyrogram Message
    return res


def get_title_entity(message: Message) -> MessageEntity | None: # Return type changed
    if message.entities: # Check if entities exist
        for e in message.entities:
            # Pyrogram uses e.type and e.url
            if e.type == MessageEntityType.TEXT_LINK and e.url in (OLD_TITLE_URL, TITLE_URL):
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


async def send_error(chat_id_or_username) -> None: # Parameter can be chat_id or username
    exc = ''.join(tb.format_exception(*sys.exc_info()))
    if len(exc) > 4000: # Keep it within reasonable limits for a message
        exc = exc[:3950] + '…' # Adjusted for header and code tags
    
    # Pyrogram's send_message
    # parse_mode is an enum
    await app.client.send_message(
        chat_id=chat_id_or_username,
        text=f'{FORMATTED_ERROR_HEADER}\n\n<code>{exc}</code>',
        link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        parse_mode=ParseMode.HTML,
    )


__all__ = [
    'Utf16CodepointsWrapper', # Added Utf16CodepointsWrapper to __all__
    'edit_message',
    'send_error',
    'get_title_entity' # Added get_title_entity to __all__
]
