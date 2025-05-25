import sys
import traceback as tb

import pyrogram
from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.types import Message, MessageEntity

from tgpy import app, reactions_fix
from tgpy.api.utils import Utf16CodepointsWrapper

TITLE = 'TGPy>'
RUNNING_TITLE = 'TGPy running>'
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
