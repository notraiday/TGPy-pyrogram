from dataclasses import dataclass

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from tgpy.api.utils import Utf16CodepointsWrapper


@dataclass
class MessageParseResult:
    is_tgpy_message: bool
    code: str | None
    result: str | None


def _get_united_code_entity(message: Message) -> MessageEntity | None:
    last_entity = None
    for entity in message.entities or []:
        if entity.type != MessageEntityType.PRE or entity.language != 'python':
            continue
        if last_entity is None:
            last_entity = entity
        elif last_entity.offset + last_entity.length + 1 == entity.offset:
            last_entity.length += entity.length + 1
    return last_entity


def parse_tgpy_message(message: Message) -> MessageParseResult:
    e = _get_united_code_entity(message)
    if not e or e.offset != 0:
        return MessageParseResult(False, None, None)
    if message.text:
        msg_text_str = message.text
    elif message.caption:
        msg_text_str = message.caption
    else:
        msg_text_str = ''
    msg_text = Utf16CodepointsWrapper(msg_text_str)
    code = msg_text[e.offset : e.offset + e.length].strip()
    remainder = str(msg_text[e.offset + e.length :])
    _, separator, result = remainder.partition('>')
    if not separator:
        return MessageParseResult(False, None, None)
    return MessageParseResult(True, code, result.strip())


__all__ = ['MessageParseResult', 'parse_tgpy_message']
