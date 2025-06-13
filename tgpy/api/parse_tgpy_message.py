from dataclasses import dataclass

from pyrogram.types import Message

from tgpy._core.message_design import (
    Utf16CodepointsWrapper,
    get_united_code_entity,
)


@dataclass
class MessageParseResult:
    is_tgpy_message: bool
    code: str | None
    result: str | None


def parse_tgpy_message(message: Message) -> MessageParseResult:
    e = get_united_code_entity(message)
    if not e or e.offset != 0:
        return MessageParseResult(False, None, None)
    if message.text:
        msg_text_str = message.text
    elif message.caption:
        msg_text_str = message.caption
    else:
        msg_text_str = ''
    msg_text = Utf16CodepointsWrapper(msg_text_str)
    code = msg_text[e.offset : e.length].strip()
    result = msg_text[msg_text.find('>', e.offset + e.length) + 1 :].strip()
    return MessageParseResult(True, code, result)


__all__ = ['MessageParseResult', 'parse_tgpy_message']
